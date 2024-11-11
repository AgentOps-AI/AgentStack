from crewai_tools import DirectorySearchTool

# dir_search_tool = DirectorySearchTool(
#     config=dict(
#         llm=dict(
#             provider="ollama",
#             config=dict(
#                 model="llama2",
#                 # temperature=0.5,
#                 # top_p=1,
#                 # stream=true,
#             ),
#         ),
#         embedder=dict(
#             provider="google",
#             config=dict(
#                 model="models/embedding-001",
#                 task_type="retrieval_document",
#                 # title="Embeddings",
#             ),
#         ),
#     )
# )

dir_search_tool = DirectorySearchTool()