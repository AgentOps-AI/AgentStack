Tool Configuration Files
========================
Tools are configured for installation & removal using JSON files in this directory. 

## Parameters

### `name` (string) [required]
The name of the tool in snake_case. This is used to identify the tool in the system.

### `cta` (string) [optional]
String to print in the terminal when the tool is installed that provides a call to action.

### `tools` (list) [required]
List of public methods that are accessible in the tool implementation.

### `env` (string) [optional]
Definitions for environment variables that will be appended to the local `.env` file.
Separate multiple environment variables with a newline character.

### `packages` (list) [optional]
A list of package names to install. These are the names of the packages that will 
be installed and removed by the package manager.

### `post_install` (string) [optional]
Shell command that will be executed after packages have been installed and environment 
variables have been set.

### `post_remove` (string) [optional]
Shell command that will be executed after the tool has been removed.

### `tools_bundled` (boolean) [optional]
Include all bundled tools in the tool implementation. 

