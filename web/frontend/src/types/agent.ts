export interface Tool {
  name: string;
  description: string;
  id: string;
}

export interface Agent {
  name: string;
  description: string;
  tools: Tool[];
}
