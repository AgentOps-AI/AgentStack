# job_posting
_An example project built with AgentStack_

## Commands used to create this project

```bash
agentstack init job_posting
agentstack g a research_agent
agentstack g a writer_agent
agentstack g a review_agent
agentstack g t research_company_culture_task
agentstack g t research_role_requirements_task
agentstack g t draft_job_posting_task
agentstack g t review_and_edit_job_posting_task
agentstack g t industry_analysis_task
```

## Other work
- Prompt engineering was done in `agents.yaml` and `tasks.yaml`
- Inputs were modified in `crew.py`

## Run this agent
```bash
agentstack run
```