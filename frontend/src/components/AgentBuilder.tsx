import React from 'react';
import { Box, Button, TextInput, MultiSelect } from '@mantine/core';
import { useForm } from '@mantine/form';

interface AgentBuilderProps {
  onSubmit: (values: { prompt: string; tools: string[] }) => void;
}

export function AgentBuilder({ onSubmit }: AgentBuilderProps) {
  const form = useForm({
    initialValues: {
      prompt: '',
      tools: [] as string[],
    },
  });

  return (
    <Box component="form" onSubmit={form.onSubmit(onSubmit)}>
      <TextInput
        label="What would you like your agent to do?"
        placeholder="Enter your request..."
        {...form.getInputProps('prompt')}
      />
      <MultiSelect
        label="Select Tools"
        placeholder="Choose tools for your agent"
        data={[]}
        {...form.getInputProps('tools')}
      />
      <Button type="submit" mt="md">
        Create Agent
      </Button>
    </Box>
  );
}
