# Repository Documentation

## `backend\services\export_doc.py`

**Export Document Function**
==========================

### Purpose

The `export_document` function converts Markdown text into a file and returns the file path. This allows users to save exported content in a format that can be easily shared or referenced.

### Important Classes/Functions

*   `markdown_to_html()`: Converts Markdown text into HTML.
*   `save_file()`: Saves an HTML file to a specified location.

### Function Signature
```markdown
export_document(markdown_text: string): string
```

### Parameters

| Parameter | Description |
| --- | --- |
| `markdown_text` | The Markdown text to be converted and saved. |

### Return Value

The file path where the exported document is saved.

### Example Usage
```python
import export_document

# Convert Markdown text to HTML
html = markdown_to_html("This is a sample #heading")

# Save the HTML to a file
file_path = export_document(html)

print(file_path)  # Output: /

## `backend\services\language.py`

**Language Detection Function**
=====================================

### Purpose

The `detect_language` function determines the language of a given text input. It returns the detected language as a string.

### Why it exists

In today's globalized world, understanding the language of text is crucial for various applications such as translation, content moderation, and sentiment analysis. This function provides a simple way to identify the language of text, making it easier to process and analyze linguistic data.

### Important Classes/Functions

* `detect_language(text)`: Takes a string input `text` and returns the detected language as a string.
	+ Example: `print(detect_language("Hello, how are you?"))` outputs "en" (English)

Note: The actual output may vary depending on the input text.

## `backend\services\doc_gen.py`

**FileInfo and Generation Tools Documentation**
=============================================

Overview
--------

This documentation provides an overview of the FileInfo class and various generation tools, including functions for file processing, repository cloning, and API management.

### FileInfo Class

Represents a processed file with its content. This class is used to store and manage information about files that have been processed by the system.

*   **Attributes:** Not explicitly defined in this documentation.
*   **Methods:** Not applicable in this documentation.

### Generation Tools

#### Functions

| Function | Description |
| --- | --- |
| `start_generation` | Starts a new generation process. (No description) |
| `should_skip` | Fast path filtering using set lookups. Returns True if the file should be skipped, False otherwise. |
| `safe_rmtree` | Cross-platform safe directory removal. Removes a directory and its contents without throwing errors. |
| `clone_repository` | Clones a repository with authentication support. (No description) |
|

## `backend\services\themes.py`

**Prompt Builder Function**
==========================

### Purpose

The `build_prompt` function generates a prompt for a machine learning model. Its primary goal is to elicit specific and relevant responses from the model.

### Functionality

* Takes input parameters (e.g., question, topic, tone) to customize the prompt.
* Returns a formatted string representing the generated prompt.

### Important Classes/Functions

* `build_prompt`: The main function responsible for generating prompts.
* Input parameters: `question`, `topic`, `tone` (optional)

### Example Usage
```markdown
# Generate a prompt for a question-and-answer model
prompt = build_prompt(question="What is the capital of France?", topic="Geography")
print(prompt)
```

Output:
```
"Ask the model to identify the capital of France within the context of geography."
```

Note: The actual output may vary depending on the input parameters.

## `backend\services\caching.py`

**Repository Management Documentation**
=====================================

### Overview

This documentation provides an overview of the repository management functions and classes used in the project.

### Classes and Functions

#### Classes

* **RepoCache**: A cache class that stores repository metadata.
* **StorageDir**: A directory class responsible for storing and retrieving data.

#### Functions

| Function | Description |
| --- | --- |
| `get_latest_commit_hash` | Returns the hash of the latest commit. |
| `init_db` | Initializes the database. |
| `get_db` | Returns a reference to the database. |
| `sanitize_filename` | Converts URLs or strings into safe filenames by removing unsafe characters. |
| `get_repo_name_from_url` | Makes a safe short repo name from URL. |
| `storage_dir` | Returns the storage directory path. |
| `get_commit_hash` | Returns the hash of a commit. |
| `save_final_doc_to_storage` | Saves a final document to storage

## `backend\services\auth.py`

**Authentication and Authorization System Documentation**
===========================================================

**Overview**
------------

This system provides a basic authentication and authorization framework for users. It allows users to create accounts, log in, and access their profile information.

**Classes**
-----------

### User

Represents a user in the system.

### GitHubAccount

Represents a user's GitHub account.

### SignupIn
### TokenOut
### UserOut

These classes are used internally by the system and do not need to be referenced directly.

**Functions**
-------------

### get_db

Returns a database connection.

### hash_password

Hashes a password for secure storage.

### verify_password

Verifies a password against a stored hash.

### create_access_token

Generates an access token for a user.

### encrypt_token
### decrypt_token

Encrypts and decrypts tokens, respectively.

### get_user_by_email
### get_user_by_id
### get_current_user

Retrieve users by email, ID, or current session.

### signup
