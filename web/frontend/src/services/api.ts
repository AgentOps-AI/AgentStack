import { Agent, Tool } from '../types/agent';

const API_BASE_URL = 'http://localhost:8000';

export const fetchTools = async (): Promise<Tool[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/tools`);
    if (!response.ok) {
      throw new Error('Failed to fetch tools');
    }
    const tools = await response.json();
    return tools.map((tool: any) => ({
      id: tool.name,
      name: tool.name,
      description: tool.category,
    }));
  } catch (error) {
    console.error('Error fetching tools:', error);
    throw error;
  }
};

export const createAgent = async (prompt: string, selectedTools: string[]): Promise<Agent> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agents`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt, tools: selectedTools }),
    });

    if (!response.ok) {
      throw new Error('Failed to create agent');
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating agent:', error);
    throw error;
  }
};
