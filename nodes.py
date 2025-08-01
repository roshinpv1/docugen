import os
import re
import yaml
from pocketflow import Node, BatchNode
from utils.crawl_github_files import crawl_github_files
from utils.call_llm import call_llm
from utils.crawl_local_files import crawl_local_files


# Helper to get content for specific file indices
def get_content_for_indices(files_data, indices):
    content_map = {}
    for i in indices:
        if 0 <= i < len(files_data):
            path, content = files_data[i]
            content_map[f"{i} # {path}"] = (
                content  # Use index + path as key for context
            )
    return content_map


class FetchRepo(Node):
    def prep(self, shared):
        repo_url = shared.get("repo_url")
        local_dir = shared.get("local_dir")
        project_name = shared.get("project_name")

        if not project_name:
            # Basic name derivation from URL or directory
            if repo_url:
                project_name = repo_url.split("/")[-1].replace(".git", "")
            else:
                project_name = os.path.basename(os.path.abspath(local_dir))
            shared["project_name"] = project_name

        # Get file patterns directly from shared
        include_patterns = shared["include_patterns"]
        exclude_patterns = shared["exclude_patterns"]
        max_file_size = shared["max_file_size"]

        return {
            "repo_url": repo_url,
            "local_dir": local_dir,
            "token": shared.get("github_token"),
            "branch": shared.get("branch", "main"),  # Add branch parameter
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns,
            "max_file_size": max_file_size,
            "use_relative_paths": True,
        }

    def exec(self, prep_res):
        if prep_res["repo_url"]:
            print(f"Crawling repository: {prep_res['repo_url']} (branch: {prep_res['branch']})...")
            result = crawl_github_files(
                repo_url=prep_res["repo_url"],
                token=prep_res["token"],
                branch=prep_res["branch"],  # Pass branch parameter
                include_patterns=prep_res["include_patterns"],
                exclude_patterns=prep_res["exclude_patterns"],
                max_file_size=prep_res["max_file_size"],
                use_relative_paths=prep_res["use_relative_paths"],
            )
        else:
            print(f"Crawling directory: {prep_res['local_dir']}...")

            result = crawl_local_files(
                directory=prep_res["local_dir"],
                include_patterns=prep_res["include_patterns"],
                exclude_patterns=prep_res["exclude_patterns"],
                max_file_size=prep_res["max_file_size"],
                use_relative_paths=prep_res["use_relative_paths"]
            )

        # Convert dict to list of tuples: [(path, content), ...]
        files_list = list(result.get("files", {}).items())
        if len(files_list) == 0:
            raise (ValueError("Failed to fetch files"))
        print(f"Fetched {len(files_list)} files.")
        return files_list

    def post(self, shared, prep_res, exec_res):
        shared["files"] = exec_res  # List of (path, content) tuples


class IdentifyAbstractions(Node):
    def prep(self, shared):
        files_data = shared["files"]
        project_name = shared["project_name"]  # Get project name
        language = shared.get("language", "english")  # Get language
        use_cache = shared.get("use_cache", True)  # Get use_cache flag, default to True
        max_abstraction_num = shared.get("max_abstraction_num", 10)  # Get max_abstraction_num, default to 10

        # Helper to create context from files, respecting limits (basic example)
        def create_llm_context(files_data):
            context = ""
            file_info = []  # Store tuples of (index, path)
            for i, (path, content) in enumerate(files_data):
                entry = f"--- File Index {i}: {path} ---\n{content}\n\n"
                context += entry
                file_info.append((i, path))

            return context, file_info  # file_info is list of (index, path)

        context, file_info = create_llm_context(files_data)
        # Format file info for the prompt (comment is just a hint for LLM)
        file_listing_for_prompt = "\n".join(
            [f"- {idx} # {path}" for idx, path in file_info]
        )
        return (
            context,
            file_listing_for_prompt,
            len(files_data),
            project_name,
            language,
            use_cache,
            max_abstraction_num,
            shared.get("timeout", 600),  # Add timeout from shared state
        )  # Return all parameters

    def exec(self, prep_res):
        (
            context,
            file_listing_for_prompt,
            file_count,
            project_name,
            language,
            use_cache,
            max_abstraction_num,
            timeout,
        ) = prep_res  # Unpack all parameters
        print(f"Identifying abstractions using LLM...")

        # Add language instruction and hints only if not English
        language_instruction = ""
        name_lang_hint = ""
        desc_lang_hint = ""
        if language.lower() != "english":
            language_instruction = f"IMPORTANT: Generate the `name` and `description` for each abstraction in **{language.capitalize()}** language. Do NOT use English for these fields.\n\n"
            # Keep specific hints here as name/description are primary targets
            name_lang_hint = f" (value in {language.capitalize()})"
            desc_lang_hint = f" (value in {language.capitalize()})"

        prompt = f"""
For the project `{project_name}`:

Codebase Context:
{context}

{language_instruction}Analyze the codebase context to identify the core technical architecture components.

Focus on identifying:
1. **API Endpoints** - REST/GraphQL endpoints, routes, handlers
2. **Core Libraries & Dependencies** - Key frameworks, libraries, and external integrations
3. **Data Models & Schemas** - Database models, data structures, schemas
4. **Service Layer** - Business logic services, utilities, helpers
5. **Configuration & Setup** - Configuration files, environment setup, deployment
6. **Middleware & Interceptors** - Authentication, logging, error handling
7. **Database & Storage** - Database connections, repositories, data access
8. **External Integrations** - Third-party APIs, webhooks, integrations

Identify the top 5-{max_abstraction_num} most important technical components that developers need to understand.

For each component, provide:
1. A concise `name`{name_lang_hint} (e.g., "User Authentication Service", "Product API Endpoints", "Database Models").
2. A technical `description` explaining its purpose, key methods/functions, and how it fits into the architecture{desc_lang_hint}.
3. A list of relevant `file_indices` (integers) using the format `idx # path/comment`.

List of file indices and paths present in the context:
{file_listing_for_prompt}

Format the output as a YAML list of dictionaries:

```yaml
- name: |
    User Authentication Service{name_lang_hint}
  description: |
    Handles user authentication and authorization. Includes login/logout endpoints,
    JWT token management, and user session handling. Key methods: authenticate(),
    generateToken(), validateSession().{desc_lang_hint}
  file_indices:
    - 0 # auth/service.py
    - 3 # auth/middleware.py
- name: |
    Product API Endpoints{name_lang_hint}
  description: |
    RESTful API endpoints for product management. Includes CRUD operations,
    search functionality, and product categorization. Routes: GET /products,
    POST /products, PUT /products/:id.{desc_lang_hint}
  file_indices:
    - 5 # api/products.py
# ... up to {max_abstraction_num} technical components
```"""
        response = call_llm(prompt, timeout=timeout)  # Use cache only if enabled and not retrying

        # --- Validation ---
        yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
        abstractions = yaml.safe_load(yaml_str)

        if not isinstance(abstractions, list):
            raise ValueError("LLM Output is not a list")

        validated_abstractions = []
        for item in abstractions:
            if not isinstance(item, dict) or not all(
                k in item for k in ["name", "description", "file_indices"]
            ):
                raise ValueError(f"Missing keys in abstraction item: {item}")
            if not isinstance(item["name"], str):
                raise ValueError(f"Name is not a string in item: {item}")
            if not isinstance(item["description"], str):
                raise ValueError(f"Description is not a string in item: {item}")
            if not isinstance(item["file_indices"], list):
                raise ValueError(f"file_indices is not a list in item: {item}")

            # Validate indices
            validated_indices = []
            for idx_entry in item["file_indices"]:
                try:
                    if isinstance(idx_entry, int):
                        idx = idx_entry
                    elif isinstance(idx_entry, str) and "#" in idx_entry:
                        idx = int(idx_entry.split("#")[0].strip())
                    else:
                        idx = int(str(idx_entry).strip())

                    if not (0 <= idx < file_count):
                        raise ValueError(
                            f"Invalid file index {idx} found in item {item['name']}. Max index is {file_count - 1}."
                        )
                    validated_indices.append(idx)
                except (ValueError, TypeError):
                    raise ValueError(
                        f"Could not parse index from entry: {idx_entry} in item {item['name']}"
                    )

            item["files"] = sorted(list(set(validated_indices)))
            # Store only the required fields
            validated_abstractions.append(
                {
                    "name": item["name"],  # Potentially translated name
                    "description": item[
                        "description"
                    ],  # Potentially translated description
                    "files": item["files"],
                }
            )

        print(f"Identified {len(validated_abstractions)} abstractions.")
        return validated_abstractions

    def post(self, shared, prep_res, exec_res):
        shared["abstractions"] = (
            exec_res  # List of {"name": str, "description": str, "files": [int]}
        )


class AnalyzeRelationships(Node):
    def prep(self, shared):
        abstractions = shared[
            "abstractions"
        ]  # Now contains 'files' list of indices, name/description potentially translated
        files_data = shared["files"]
        project_name = shared["project_name"]  # Get project name
        language = shared.get("language", "english")  # Get language
        use_cache = shared.get("use_cache", True)  # Get use_cache flag, default to True

        # Get the actual number of abstractions directly
        num_abstractions = len(abstractions)

        # Create context with abstraction names, indices, descriptions, and relevant file snippets
        context = "Identified Abstractions:\\n"
        all_relevant_indices = set()
        abstraction_info_for_prompt = []
        for i, abstr in enumerate(abstractions):
            # Use 'files' which contains indices directly
            file_indices_str = ", ".join(map(str, abstr["files"]))
            # Abstraction name and description might be translated already
            info_line = f"- Index {i}: {abstr['name']} (Relevant file indices: [{file_indices_str}])\\n  Description: {abstr['description']}"
            context += info_line + "\\n"
            abstraction_info_for_prompt.append(
                f"{i} # {abstr['name']}"
            )  # Use potentially translated name here too
            all_relevant_indices.update(abstr["files"])

        context += "\\nRelevant File Snippets (Referenced by Index and Path):\\n"
        # Get content for relevant files using helper
        relevant_files_content_map = get_content_for_indices(
            files_data, sorted(list(all_relevant_indices))
        )
        # Format file content for context
        file_context_str = "\\n\\n".join(
            f"--- File: {idx_path} ---\\n{content}"
            for idx_path, content in relevant_files_content_map.items()
        )
        context += file_context_str

        return (
            context,
            "\n".join(abstraction_info_for_prompt),
            num_abstractions, # Pass the actual count
            project_name,
            language,
            use_cache,
            shared.get("timeout", 600),  # Add timeout from shared state
        )  # Return use_cache

    def exec(self, prep_res):
        (
            context,
            abstraction_listing,
            num_abstractions, # Receive the actual count
            project_name,
            language,
            use_cache,
            timeout,
         ) = prep_res  # Unpack use_cache
        print(f"Analyzing relationships using LLM...")

        # Add language instruction and hints only if not English
        language_instruction = ""
        lang_hint = ""
        list_lang_note = ""
        if language.lower() != "english":
            language_instruction = f"IMPORTANT: Generate the `summary` and relationship `label` fields in **{language.capitalize()}** language. Do NOT use English for these fields.\n\n"
            lang_hint = f" (in {language.capitalize()})"
            list_lang_note = f" (Names might be in {language.capitalize()})"  # Note for the input list

        prompt = f"""
Based on the following technical components and relevant code snippets from the project `{project_name}`:

List of Technical Component Indices and Names{list_lang_note}:
{abstraction_listing}

Context (Technical Components, Descriptions, Code):
{context}

{language_instruction}Please provide:
1. A technical `summary` of the project's architecture, main technologies used, and system design{lang_hint}. Focus on:
   - **Technology Stack**: Frameworks, libraries, databases used
   - **Architecture Pattern**: MVC, microservices, monolith, etc.
   - **Key Features**: Main functionality and capabilities
   - **Deployment**: How the system is deployed and scaled
   Use markdown formatting with **bold** and *italic* text to highlight important technical concepts.

2. A list (`relationships`) describing the technical dependencies and data flow between components. For each relationship, specify:
    - `from_abstraction`: Index of the source component (e.g., `0 # UserAuthService`)
    - `to_abstraction`: Index of the target component (e.g., `1 # DatabaseModels`)
    - `label`: A technical relationship label **in just a few words**{lang_hint} (e.g., "Authenticates", "Stores Data", "Calls API", "Depends On", "Uses Library").
    Focus on technical relationships like:
    - API calls between services
    - Database dependencies
    - Library/framework usage
    - Data flow between components
    - Authentication/authorization flows
    - External service integrations

IMPORTANT: Make sure EVERY technical component is involved in at least ONE relationship (either as source or target). Each component index must appear at least once across all relationships.

Format the output as YAML:

```yaml
summary: |
  **Technology Stack**: Node.js/Express backend with React frontend, PostgreSQL database, Redis caching.
  **Architecture**: RESTful API with MVC pattern, JWT authentication, microservices for user management.
  **Key Features**: User authentication, product catalog, order processing, payment integration.
  **Deployment**: Docker containers on AWS ECS with auto-scaling.{lang_hint}
relationships:
  - from_abstraction: 0 # UserAuthService
    to_abstraction: 1 # DatabaseModels
    label: "Stores User Data"{lang_hint}
  - from_abstraction: 2 # ProductAPI
    to_abstraction: 1 # DatabaseModels
    label: "Queries Products"{lang_hint}
  - from_abstraction: 0 # UserAuthService
    to_abstraction: 3 # JWTMiddleware
    label: "Uses JWT"{lang_hint}
  # ... other technical relationships
```

Now, provide the YAML output:
"""
        response = call_llm(prompt, timeout=timeout) # Use cache only if enabled and not retrying

        # --- Validation ---
        yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
        relationships_data = yaml.safe_load(yaml_str)

        if not isinstance(relationships_data, dict) or not all(
            k in relationships_data for k in ["summary", "relationships"]
        ):
            raise ValueError(
                "LLM output is not a dict or missing keys ('summary', 'relationships')"
            )
        if not isinstance(relationships_data["summary"], str):
            raise ValueError("summary is not a string")
        if not isinstance(relationships_data["relationships"], list):
            raise ValueError("relationships is not a list")

        # Validate relationships structure
        validated_relationships = []
        for rel in relationships_data["relationships"]:
            # Check for 'label' key
            if not isinstance(rel, dict) or not all(
                k in rel for k in ["from_abstraction", "to_abstraction", "label"]
            ):
                print(f"Warning: Skipping invalid relationship structure: {rel}")
                continue
            # Validate 'label' is a string
            if not isinstance(rel["label"], str):
                print(f"Warning: Skipping relationship with invalid label: {rel}")
                continue

            # Validate indices
            try:
                from_idx = int(str(rel["from_abstraction"]).split("#")[0].strip())
                to_idx = int(str(rel["to_abstraction"]).split("#")[0].strip())
                if not (
                    0 <= from_idx < num_abstractions and 0 <= to_idx < num_abstractions
                ):
                    print(f"Warning: Skipping relationship with out-of-bounds indices: from={from_idx}, to={to_idx}. Max index is {num_abstractions-1}.")
                    continue
                validated_relationships.append(
                    {
                        "from": from_idx,
                        "to": to_idx,
                        "label": rel["label"],  # Potentially translated label
                    }
                )
            except (ValueError, TypeError):
                print(f"Warning: Skipping relationship with unparseable indices: {rel}")
                continue

        # Ensure we have at least some valid relationships
        if not validated_relationships:
            print("Warning: No valid relationships found. Creating default relationships.")
            # Create default relationships to ensure each abstraction is connected
            for i in range(num_abstractions):
                for j in range(i + 1, num_abstractions):
                    validated_relationships.append({
                        "from": i,
                        "to": j,
                        "label": "Related to"
                    })
                    break  # Only create one relationship per abstraction

        print("Generated project summary and relationship details.")
        return {
            "summary": relationships_data["summary"],  # Potentially translated summary
            "details": validated_relationships,  # Store validated, index-based relationships with potentially translated labels
        }

    def post(self, shared, prep_res, exec_res):
        # Structure is now {"summary": str, "details": [{"from": int, "to": int, "label": str}]}
        # Summary and label might be translated
        shared["relationships"] = exec_res


class OrderChapters(Node):
    def prep(self, shared):
        abstractions = shared["abstractions"]  # Name/description might be translated
        relationships = shared["relationships"]  # Summary/label might be translated
        project_name = shared["project_name"]  # Get project name
        language = shared.get("language", "english")  # Get language
        use_cache = shared.get("use_cache", True)  # Get use_cache flag, default to True

        # Prepare context for the LLM
        abstraction_info_for_prompt = []
        for i, a in enumerate(abstractions):
            abstraction_info_for_prompt.append(
                f"- {i} # {a['name']}"
            )  # Use potentially translated name
        abstraction_listing = "\n".join(abstraction_info_for_prompt)

        # Use potentially translated summary and labels
        summary_note = ""
        if language.lower() != "english":
            summary_note = (
                f" (Note: Project Summary might be in {language.capitalize()})"
            )

        context = f"Project Summary{summary_note}:\n{relationships['summary']}\n\n"
        context += "Relationships (Indices refer to abstractions above):\n"
        for rel in relationships["details"]:
            from_name = abstractions[rel["from"]]["name"]
            to_name = abstractions[rel["to"]]["name"]
            # Use potentially translated 'label'
            context += f"- From {rel['from']} ({from_name}) to {rel['to']} ({to_name}): {rel['label']}\n"  # Label might be translated

        list_lang_note = ""
        if language.lower() != "english":
            list_lang_note = f" (Names might be in {language.capitalize()})"

        return (
            abstraction_listing,
            context,
            len(abstractions),
            project_name,
            list_lang_note,
            use_cache,
            shared.get("timeout", 600),  # Add timeout from shared state
        )  # Return use_cache

    def exec(self, prep_res):
        (
            abstraction_listing,
            context,
            num_abstractions,
            project_name,
            list_lang_note,
            use_cache,
            timeout,
        ) = prep_res  # Unpack use_cache
        print("Determining chapter order using LLM...")
        # No language variation needed here in prompt instructions, just ordering based on structure
        # The input names might be translated, hence the note.
        prompt = f"""
Given the following project abstractions and their relationships for the project ```` {project_name} ````:

Abstractions (Index # Name){list_lang_note}:
{abstraction_listing}

Context about relationships and project summary:
{context}

If you are going to make a tutorial for ```` {project_name} ````, what is the best order to explain these abstractions, from first to last?
Ideally, first explain those that are the most important or foundational, perhaps user-facing concepts or entry points. Then move to more detailed, lower-level implementation details or supporting concepts.

Output the ordered list of abstraction indices, including the name in a comment for clarity. Use the format `idx # AbstractionName`.

```yaml
- 2 # FoundationalConcept
- 0 # CoreClassA
- 1 # CoreClassB (uses CoreClassA)
- ...
```

Now, provide the YAML output:
"""
        response = call_llm(prompt, timeout=timeout) # Use cache only if enabled and not retrying

        # --- Validation ---
        yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
        ordered_indices_raw = yaml.safe_load(yaml_str)

        if not isinstance(ordered_indices_raw, list):
            raise ValueError("LLM output is not a list")

        ordered_indices = []
        seen_indices = set()
        for entry in ordered_indices_raw:
            try:
                if isinstance(entry, int):
                    idx = entry
                elif isinstance(entry, str) and "#" in entry:
                    idx = int(entry.split("#")[0].strip())
                else:
                    idx = int(str(entry).strip())

                if not (0 <= idx < num_abstractions):
                    print(f"Warning: Skipping invalid index {idx} in ordered list. Max index is {num_abstractions-1}.")
                    continue
                if idx in seen_indices:
                    print(f"Warning: Skipping duplicate index {idx} in ordered list.")
                    continue
                ordered_indices.append(idx)
                seen_indices.add(idx)

            except (ValueError, TypeError):
                print(f"Warning: Skipping unparseable entry in ordered list: {entry}")
                continue

        # Check if we have enough valid indices
        if len(ordered_indices) != num_abstractions:
            print(f"Warning: Ordered list incomplete. Got {len(ordered_indices)} indices, expected {num_abstractions}.")
            # Add missing indices in order
            for i in range(num_abstractions):
                if i not in seen_indices:
                    ordered_indices.append(i)
                    print(f"Added missing index: {i}")
            
            # Ensure we have the right number of indices
            if len(ordered_indices) != num_abstractions:
                print(f"Error: Still missing indices after adding defaults. Got {len(ordered_indices)}, expected {num_abstractions}")
                # Create a simple default order
                ordered_indices = list(range(num_abstractions))

        # Check if all abstractions are included
        if len(ordered_indices) != num_abstractions:
            print(f"Warning: Final ordered list has {len(ordered_indices)} indices, expected {num_abstractions}. Using default order.")
            ordered_indices = list(range(num_abstractions))

        print(f"Determined chapter order (indices): {ordered_indices}")
        return ordered_indices  # Return the list of indices

    def post(self, shared, prep_res, exec_res):
        # exec_res is already the list of ordered indices
        shared["chapter_order"] = exec_res  # List of indices


class WriteChapters(BatchNode):
    def prep(self, shared):
        chapter_order = shared["chapter_order"]  # List of indices
        abstractions = shared[
            "abstractions"
        ]  # List of {"name": str, "description": str, "files": [int]}
        files_data = shared["files"]  # List of (path, content) tuples
        project_name = shared["project_name"]
        language = shared.get("language", "english")
        use_cache = shared.get("use_cache", True)  # Get use_cache flag, default to True

        # Get already written chapters to provide context
        # We store them temporarily during the batch run, not in shared memory yet
        # The 'previous_chapters_summary' will be built progressively in the exec context
        self.chapters_written_so_far = (
            []
        )  # Use instance variable for temporary storage across exec calls

        # Create a complete list of all chapters
        all_chapters = []
        chapter_filenames = {}  # Store chapter filename mapping for linking
        for i, abstraction_index in enumerate(chapter_order):
            if 0 <= abstraction_index < len(abstractions):
                chapter_num = i + 1
                chapter_name = abstractions[abstraction_index][
                    "name"
                ]  # Potentially translated name
                # Create safe filename (from potentially translated name)
                safe_name = "".join(
                    c if c.isalnum() else "_" for c in chapter_name
                ).lower()
                filename = f"{i+1:02d}_{safe_name}.md"
                # Format with link (using potentially translated name)
                all_chapters.append(f"{chapter_num}. [{chapter_name}]({filename})")
                # Store mapping of chapter index to filename for linking
                chapter_filenames[abstraction_index] = {
                    "num": chapter_num,
                    "name": chapter_name,
                    "filename": filename,
                }

        # Create a formatted string with all chapters
        full_chapter_listing = "\n".join(all_chapters)

        items_to_process = []
        for i, abstraction_index in enumerate(chapter_order):
            if 0 <= abstraction_index < len(abstractions):
                abstraction_details = abstractions[
                    abstraction_index
                ]  # Contains potentially translated name/desc
                # Use 'files' (list of indices) directly
                related_file_indices = abstraction_details.get("files", [])
                # Get content using helper, passing indices
                related_files_content_map = get_content_for_indices(
                    files_data, related_file_indices
                )

                # Get previous chapter info for transitions (uses potentially translated name)
                prev_chapter = None
                if i > 0:
                    prev_idx = chapter_order[i - 1]
                    prev_chapter = chapter_filenames[prev_idx]

                # Get next chapter info for transitions (uses potentially translated name)
                next_chapter = None
                if i < len(chapter_order) - 1:
                    next_idx = chapter_order[i + 1]
                    next_chapter = chapter_filenames[next_idx]

                items_to_process.append(
                    {
                        "chapter_num": i + 1,
                        "abstraction_index": abstraction_index,
                        "abstraction_details": abstraction_details,  # Has potentially translated name/desc
                        "related_files_content_map": related_files_content_map,
                        "project_name": shared["project_name"],  # Add project name
                        "full_chapter_listing": full_chapter_listing,  # Add the full chapter listing (uses potentially translated names)
                        "chapter_filenames": chapter_filenames,  # Add chapter filenames mapping (uses potentially translated names)
                        "prev_chapter": prev_chapter,  # Add previous chapter info (uses potentially translated name)
                        "next_chapter": next_chapter,  # Add next chapter info (uses potentially translated name)
                        "language": language,  # Add language for multi-language support
                        "use_cache": use_cache, # Pass use_cache flag
                        "timeout": shared.get("timeout", 600),  # Add timeout from shared state
                        # previous_chapters_summary will be added dynamically in exec
                    }
                )
            else:
                print(
                    f"Warning: Invalid abstraction index {abstraction_index} in chapter_order. Skipping."
                )

        print(f"Preparing to write {len(items_to_process)} chapters...")
        return items_to_process  # Iterable for BatchNode

    def exec(self, item):
        # This runs for each item prepared above
        abstraction_name = item["abstraction_details"][
            "name"
        ]  # Potentially translated name
        abstraction_description = item["abstraction_details"][
            "description"
        ]  # Potentially translated description
        chapter_num = item["chapter_num"]
        project_name = item.get("project_name")
        language = item.get("language", "english")
        use_cache = item.get("use_cache", True) # Read use_cache from item
        timeout = item.get("timeout", 600) # Read timeout from item
        print(f"Writing chapter {chapter_num} for: {abstraction_name} using LLM...")

        # Prepare file context string from the map
        file_context_str = "\n\n".join(
            f"--- File: {idx_path.split('# ')[1] if '# ' in idx_path else idx_path} ---\n{content}"
            for idx_path, content in item["related_files_content_map"].items()
        )

        # Get summary of chapters written *before* this one
        # Use the temporary instance variable
        previous_chapters_summary = "\n---\n".join(self.chapters_written_so_far)

        # Add language instruction and context notes only if not English
        language_instruction = ""
        concept_details_note = ""
        structure_note = ""
        prev_summary_note = ""
        instruction_lang_note = ""
        mermaid_lang_note = ""
        code_comment_note = ""
        link_lang_note = ""
        tone_note = ""
        if language.lower() != "english":
            lang_cap = language.capitalize()
            language_instruction = f"IMPORTANT: Write this ENTIRE tutorial chapter in **{lang_cap}**. Some input context (like concept name, description, chapter list, previous summary) might already be in {lang_cap}, but you MUST translate ALL other generated content including explanations, examples, technical terms, and potentially code comments into {lang_cap}. DO NOT use English anywhere except in code syntax, required proper nouns, or when specified. The entire output MUST be in {lang_cap}.\n\n"
            concept_details_note = f" (Note: Provided in {lang_cap})"
            structure_note = f" (Note: Chapter names might be in {lang_cap})"
            prev_summary_note = f" (Note: This summary might be in {lang_cap})"
            instruction_lang_note = f" (in {lang_cap})"
            mermaid_lang_note = f" (Use {lang_cap} for labels/text if appropriate)"
            code_comment_note = f" (Translate to {lang_cap} if possible, otherwise keep minimal English for clarity)"
            link_lang_note = (
                f" (Use the {lang_cap} chapter title from the structure above)"
            )
            tone_note = f" (appropriate for {lang_cap} readers)"

        prompt = f"""
{language_instruction}Write a comprehensive technical documentation chapter (in Markdown format) for the project `{project_name}` about the technical component: "{abstraction_name}". This is Chapter {chapter_num}.

Technical Component Details{concept_details_note}:
- Name: {abstraction_name}
- Description:
{abstraction_description}

Complete Documentation Structure{structure_note}:
{item["full_chapter_listing"]}

Context from previous chapters{prev_summary_note}:
{previous_chapters_summary if previous_chapters_summary else "This is the first chapter."}

Relevant Code Snippets (Code itself remains unchanged):
{file_context_str if file_context_str else "No specific code snippets provided for this component."}

Instructions for the technical documentation chapter (Generate content in {language.capitalize()} unless specified otherwise):
- Start with a clear heading (e.g., `# Chapter {chapter_num}: {abstraction_name}`). Use the provided component name.

- If this is not the first chapter, begin with a brief technical transition from the previous chapter{instruction_lang_note}, referencing it with a proper Markdown link using its name{link_lang_note}.

- Begin with a technical overview explaining the component's role in the architecture{instruction_lang_note}. Focus on:
  - **Purpose**: What technical problem this component solves
  - **Architecture Role**: How it fits into the overall system design
  - **Key Responsibilities**: Main functions and capabilities
  - **Technologies Used**: Frameworks, libraries, and tools

- **API Endpoints & Interfaces**: If this component exposes APIs, document:
  - REST endpoints with HTTP methods, paths, and parameters
  - Request/response schemas and examples
  - Authentication requirements
  - Rate limiting and error handling

- **Dependencies & Libraries**: Document:
  - External libraries and frameworks used
  - Internal dependencies on other components
  - Database connections and data models
  - Third-party service integrations

- **Configuration & Setup**: Include:
  - Environment variables and configuration files
  - Installation and setup instructions
  - Deployment considerations
  - Performance tuning options

- **Code Examples**: Provide practical code examples{instruction_lang_note}:
  - Basic usage patterns
  - Common integration scenarios
  - Error handling examples
  - Best practices and patterns

- **Architecture Diagrams**: Use Mermaid diagrams to illustrate:
  - Component interactions and data flow
  - Sequence diagrams for key operations
  - Architecture patterns and design decisions
  - Integration points with other components

- **Implementation Details**: Dive into the technical implementation{instruction_lang_note}:
  - Key classes, functions, and methods
  - Data structures and algorithms used
  - Performance characteristics and optimizations
  - Security considerations and best practices

- **Testing & Debugging**: Include:
  - Unit testing strategies
  - Integration testing approaches
  - Debugging tips and common issues
  - Monitoring and logging practices

- **Performance & Scalability**: Discuss:
  - Performance bottlenecks and solutions
  - Scaling strategies and considerations
  - Resource usage and optimization
  - Caching and optimization techniques

- IMPORTANT: When you need to refer to other technical components covered in other chapters, ALWAYS use proper Markdown links like this: [Chapter Title](filename.md). Use the Complete Documentation Structure above to find the correct filename and the chapter title{link_lang_note}. Translate the surrounding text.

- Use mermaid diagrams to illustrate complex technical concepts (```mermaid``` format). {mermaid_lang_note}.

- End the chapter with a technical summary that includes:
  - Key takeaways and best practices
  - Common pitfalls to avoid
  - Next steps for further development
  - Transition to the next chapter with proper Markdown link{link_lang_note}

- Ensure the tone is professional and technical, suitable for developers and architects{tone_note}.

- Output *only* the Markdown content for this chapter.

Now, directly provide a comprehensive technical documentation output (DON'T need ```markdown``` tags):
"""
        chapter_content = call_llm(prompt, timeout=timeout) # Use cache only if enabled and not retrying
        # Basic validation/cleanup
        actual_heading = f"# Chapter {chapter_num}: {abstraction_name}"  # Use potentially translated name
        if not chapter_content.strip().startswith(f"# Chapter {chapter_num}"):
            # Add heading if missing or incorrect, trying to preserve content
            lines = chapter_content.strip().split("\n")
            if lines and lines[0].strip().startswith(
                "#"
            ):  # If there's some heading, replace it
                lines[0] = actual_heading
                chapter_content = "\n".join(lines)
            else:  # Otherwise, prepend it
                chapter_content = f"{actual_heading}\n\n{chapter_content}"

        # Add the generated content to our temporary list for the next iteration's context
        self.chapters_written_so_far.append(chapter_content)

        return chapter_content  # Return the Markdown string (potentially translated)

    def post(self, shared, prep_res, exec_res_list):
        # exec_res_list contains the generated Markdown for each chapter, in order
        shared["chapters"] = exec_res_list
        # Clean up the temporary instance variable
        del self.chapters_written_so_far
        print(f"Finished writing {len(exec_res_list)} chapters.")


class CombineTutorial(Node):
    def prep(self, shared):
        project_name = shared["project_name"]
        output_base_dir = shared.get("output_dir", "output")  # Default output dir
        output_path = os.path.join(output_base_dir, project_name)
        repo_url = shared.get("repo_url")  # Get the repository URL
        output_format = shared.get("output_format", "markdown")  # Get output format

        # Get potentially translated data
        relationships_data = shared[
            "relationships"
        ]  # {"summary": str, "details": [{"from": int, "to": int, "label": str}]} -> summary/label potentially translated
        chapter_order = shared["chapter_order"]  # indices
        abstractions = shared[
            "abstractions"
        ]  # list of dicts -> name/description potentially translated
        chapters_content = shared[
            "chapters"
        ]  # list of strings -> content potentially translated

        # --- Generate Mermaid Diagram ---
        mermaid_lines = ["flowchart TD"]
        # Add nodes for each abstraction using potentially translated names
        for i, abstr in enumerate(abstractions):
            node_id = f"A{i}"
            # Use potentially translated name, sanitize for Mermaid ID and label
            sanitized_name = abstr["name"].replace('"', "")
            node_label = sanitized_name  # Using sanitized name only
            mermaid_lines.append(
                f'    {node_id}["{node_label}"]'
            )  # Node label uses potentially translated name
        # Add edges for relationships using potentially translated labels
        for rel in relationships_data["details"]:
            from_node_id = f"A{rel['from']}"
            to_node_id = f"A{rel['to']}"
            # Use potentially translated label, sanitize
            edge_label = (
                rel["label"].replace('"', "").replace("\n", " ")
            )  # Basic sanitization
            max_label_len = 30
            if len(edge_label) > max_label_len:
                edge_label = edge_label[: max_label_len - 3] + "..."
            mermaid_lines.append(
                f'    {from_node_id} -- "{edge_label}" --> {to_node_id}'
            )  # Edge label uses potentially translated label

        mermaid_diagram = "\n".join(mermaid_lines)
        # --- End Mermaid ---

        # --- Prepare index content based on format ---
        if output_format == "html":
            # Import HTML generator
            from utils.html_generator import generate_html_index
            
            # Prepare chapter links for HTML
            chapter_links = []
            for i, abstraction_index in enumerate(chapter_order):
                if 0 <= abstraction_index < len(abstractions) and i < len(chapters_content):
                    abstraction_name = abstractions[abstraction_index]["name"]
                    safe_name = "".join(
                        c if c.isalnum() else "_" for c in abstraction_name
                    ).lower()
                    filename = f"{i+1:02d}_{safe_name}.html"
                    chapter_links.append({
                        "filename": filename,
                        "title": abstraction_name
                    })
            
            # Generate HTML index
            index_content = generate_html_index(
                project_name=project_name,
                summary=relationships_data["summary"],
                repo_url=repo_url or "",
                mermaid_diagram=mermaid_diagram,
                chapter_links=chapter_links
            )
        else:
            # Markdown format (default)
            index_content = f"# Technical Documentation: {project_name}\n\n"
            index_content += f"{relationships_data['summary']}\n\n"  # Use the potentially translated summary directly
            # Keep fixed strings in English
            index_content += f"**Source Repository:** [{repo_url}]({repo_url})\n\n"

            # Add Mermaid diagram for relationships (diagram itself uses potentially translated names/labels)
            index_content += "## Architecture Overview\n\n"
            index_content += "The following diagram shows the technical relationships between components:\n\n"
            index_content += "```mermaid\n"
            index_content += mermaid_diagram + "\n"
            index_content += "```\n\n"

            # Keep fixed strings in English
            index_content += f"## Technical Components\n\n"

        chapter_files = []
        # Generate chapter links based on the determined order, using potentially translated names
        for i, abstraction_index in enumerate(chapter_order):
            # Ensure index is valid and we have content for it
            if 0 <= abstraction_index < len(abstractions) and i < len(chapters_content):
                abstraction_name = abstractions[abstraction_index][
                    "name"
                ]  # Potentially translated name
                # Sanitize potentially translated name for filename
                safe_name = "".join(
                    c if c.isalnum() else "_" for c in abstraction_name
                ).lower()
                
                # Choose file extension based on format
                extension = ".html" if output_format == "html" else ".md"
                filename = f"{i+1:02d}_{safe_name}{extension}"
                
                if output_format == "markdown":
                    index_content += f"{i+1}. [{abstraction_name}]({filename})\n"  # Use potentially translated name in link text

                # Add attribution to chapter content (using English fixed string)
                chapter_content = chapters_content[i]  # Potentially translated content
                if not chapter_content.endswith("\n\n"):
                    chapter_content += "\n\n"
                # Keep fixed strings in English
                chapter_content += f"---\n\nGenerated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)"

                # Store filename and corresponding content
                chapter_files.append({"filename": filename, "content": chapter_content})
            else:
                print(
                    f"Warning: Mismatch between chapter order, abstractions, or content at index {i} (abstraction index {abstraction_index}). Skipping file generation for this entry."
                )

        if output_format == "markdown":
            # Add attribution to index content (using English fixed string)
            index_content += f"\n\n---\n\nGenerated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)"

        return {
            "output_path": output_path,
            "index_content": index_content,
            "chapter_files": chapter_files,  # List of {"filename": str, "content": str}
            "output_format": output_format,
        }

    def exec(self, prep_res):
        output_path = prep_res["output_path"]
        index_content = prep_res["index_content"]
        chapter_files = prep_res["chapter_files"]
        output_format = prep_res["output_format"]

        print(f"Combining technical documentation into directory: {output_path}")
        # Rely on Node's built-in retry/fallback
        os.makedirs(output_path, exist_ok=True)

        # Write index file
        index_filename = "index.html" if output_format == "html" else "index.md"
        index_filepath = os.path.join(output_path, index_filename)
        with open(index_filepath, "w", encoding="utf-8") as f:
            f.write(index_content)
        print(f"  - Wrote {index_filepath}")

        # Write chapter files
        for chapter_info in chapter_files:
            chapter_filepath = os.path.join(output_path, chapter_info["filename"])
            
            # Convert markdown to HTML if needed
            content = chapter_info["content"]
            if output_format == "html":
                from utils.html_generator import markdown_to_html
                content = markdown_to_html(content)
            
            with open(chapter_filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  - Wrote {chapter_filepath}")

        return output_path  # Return the final path

    def post(self, shared, prep_res, exec_res):
        shared["final_output_dir"] = exec_res  # Store the output path
        print(f"\nTechnical documentation generation complete! Files are in: {exec_res}")
