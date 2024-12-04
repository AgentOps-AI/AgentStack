from composio_crewai import ComposioToolSet, App

composio_tools = ComposioToolSet().get_tools(apps=[App.CODEINTERPRETER])
# composio_tools = ComposioToolSet().get_tools(apps=[App.GITHUB])
# etc

# change App.CODEINTERPRETER to be the app you want to use
# For more info on tool selection, see https://docs.agentstack.sh/tools/tool/composio
