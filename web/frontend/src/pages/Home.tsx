import React, { useState } from 'react';
import { Container, Title, Text, Paper, Alert } from '@mantine/core';
import { AgentBuilder } from '../components/AgentBuilder';
import { createAgent } from '../services/api';
import { Agent } from '../types/agent';

export function Home() {
  const [agent, setAgent] = useState<Agent | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCreateAgent = async (values: { prompt: string; tools: string[] }) => {
    try {
      const newAgent = await createAgent(values.prompt, values.tools);
      setAgent(newAgent);
      setError(null);
    } catch (err) {
      setError('Failed to create agent. Please try again.');
    }
  };

  return (
    <Container size="lg" py="xl">
      <Title order={1} mb="md">AgentStack Interface</Title>
      <Text size="lg" mb="xl">Create and configure your AI agents with ease.</Text>

      {error && (
        <Alert color="red" mb="xl" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper shadow="sm" p="xl" radius="md">
        <AgentBuilder onSubmit={handleCreateAgent} />
      </Paper>

      {agent && (
        <Paper shadow="sm" p="xl" radius="md" mt="xl">
          <Title order={2} mb="md">Created Agent</Title>
          <Text><strong>Name:</strong> {agent.name}</Text>
          <Text><strong>Description:</strong> {agent.description}</Text>
          <Text><strong>Tools:</strong></Text>
          <ul>
            {agent.tools.map((tool) => (
              <li key={tool.id}>{tool.name} - {tool.description}</li>
            ))}
          </ul>
        </Paper>
      )}
    </Container>
  );
}
