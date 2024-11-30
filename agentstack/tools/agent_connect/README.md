

Tool Implementation
===================

`config.json`
-------------
This contains the configuration for the tool for use by agentstack.

`pyproject.toml`
----------------
This contains the build configuration for the tool.

`crew`
------
Python package which contains the tool implementation specific to CrewAI.
Use relative imports to include shared code from the root of the tool's package.
Deploy/install command should handle both single files and directories.

Additional frameworks will get their own directories.



