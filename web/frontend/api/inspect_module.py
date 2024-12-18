import agentstack

print(f"AgentStack package location: {agentstack.__file__}")
print(f"AgentStack version: {agentstack.__version__}")
print("\nModule contents:")
for item in dir(agentstack):
    if not item.startswith('__'):
        print(f"- {item}")
