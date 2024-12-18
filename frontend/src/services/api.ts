import { Agent, Tool } from '../types/agent';

export const fetchTools = async (): Promise<Tool[]> => {
  // TODO: Implement actual API call to AgentStack
  return [];
};

export const createAgent = async (prompt: string, selectedTools: string[]): Promise<Agent> => {
  // TODO: Implement actual API call to AgentStack
  return {
    name: '',
    description: '',
    tools: [],
  };
};
