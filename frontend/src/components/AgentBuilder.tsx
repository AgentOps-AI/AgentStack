import React, { useEffect, useState } from 'react';
import { Box, Button, TextInput, MultiSelect, LoadingOverlay, Alert } from '@mantine/core';
import { useForm } from '@mantine/form';
import { fetchTools } from '../services/api';
import { Tool } from '../types/agent';

interface AgentBuilderProps {
  onSubmit: (values: { prompt: string; tools: string[] }) => Promise<void>;
}

export function AgentBuilder({ onSubmit }: AgentBuilderProps) {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm({
    initialValues: {
      prompt: '',
      tools: [] as string[],
    },
    validate: {
      prompt: (value) => (!value ? 'Please enter a prompt' : null),
      tools: (value) => (value.length === 0 ? 'Please select at least one tool' : null),
    },
  });

  useEffect(() => {
    const loadTools = async () => {
      try {
        setLoading(true);
        const fetchedTools = await fetchTools();
        setTools(fetchedTools);
      } catch (err) {
        setError('Failed to load tools. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    loadTools();
  }, []);

  const handleSubmit = async (values: { prompt: string; tools: string[] }) => {
    try {
      setLoading(true);
      setError(null);
      await onSubmit(values);
    } catch (err) {
      setError('Failed to create agent. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box pos="relative">
      <LoadingOverlay visible={loading} />
      {error && (
        <Alert color="red" mb="md" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      <Box component="form" onSubmit={form.onSubmit(handleSubmit)}>
        <TextInput
          label="What would you like your agent to do?"
          placeholder="Enter your request..."
          required
          mb="md"
          {...form.getInputProps('prompt')}
        />
        <MultiSelect
          label="Select Tools"
          placeholder="Choose tools for your agent"
          data={tools.map((tool) => ({
            value: tool.id,
            label: `${tool.name} - ${tool.description}`,
          }))}
          required
          mb="md"
          {...form.getInputProps('tools')}
        />
        <Button type="submit" disabled={loading}>
          {loading ? 'Creating Agent...' : 'Create Agent'}
        </Button>
      </Box>
    </Box>
  );
}
