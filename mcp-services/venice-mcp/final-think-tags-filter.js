// Final implementation of the think tags filter for Venice.ai API
function removeThinkTags(content) {
  if (!content) return "";
  
  // Handle nested <think> tags by repeatedly applying the regex until no more matches
  let previousContent = "";
  let cleanedContent = content;
  
  while (previousContent !== cleanedContent) {
    previousContent = cleanedContent;
    cleanedContent = cleanedContent.replace(/<think>[\s\S]*?<\/think>/g, '');
  }
  
  // Handle unclosed <think> tags
  if (cleanedContent.includes('<think>')) {
    const thinkIndex = cleanedContent.indexOf('<think>');
    cleanedContent = cleanedContent.substring(0, thinkIndex);
  }
  
  // Special case: entire content is within an unclosed <think> tag
  if (content.trim().startsWith('<think>') && !content.includes('</think>')) {
    // Try to extract meaningful content after the <think> tag
    const extractedContent = content.replace('<think>', '').trim();
    if (extractedContent.length > 0) {
      return extractedContent;
    }
  }
  
  // Clean up any extra spaces that might have been created
  cleanedContent = cleanedContent.replace(/\s+/g, ' ').trim();
  
  return cleanedContent.length > 0 ? cleanedContent : "I'm sorry, I couldn't generate a proper response.";
}

// Create the MCP server implementation
const veniceApiFilter = {
  name: "VeniceApiFilter",
  description: "Filters <think> tags from Venice.ai API responses",
  
  // Filter function for use in MCP server
  filterResponse(response) {
    if (!response || !response.choices || !response.choices[0] || !response.choices[0].message) {
      return response;
    }
    
    const originalContent = response.choices[0].message.content;
    const cleanedContent = removeThinkTags(originalContent);
    
    // Create a new response object with the cleaned content
    const filteredResponse = {
      ...response,
      choices: [
        {
          ...response.choices[0],
          message: {
            ...response.choices[0].message,
            content: cleanedContent
          }
        }
      ]
    };
    
    return filteredResponse;
  }
};

// Export the filter for use in MCP server
module.exports = veniceApiFilter;

// Test cases
const testCases = [
  {
    name: "Case 1: Content with <think> tags",
    input: "Hello <think>This is thinking text that should be removed</think> world!",
    expected: "Hello world!"
  },
  {
    name: "Case 2: Content starting with <think> tag",
    input: "<think>This is thinking text that should be removed</think> Hello world!",
    expected: "Hello world!"
  },
  {
    name: "Case 3: Content ending with <think> tag",
    input: "Hello world! <think>This is thinking text that should be removed</think>",
    expected: "Hello world!"
  },
  {
    name: "Case 4: Multiple <think> tags",
    input: "Hello <think>thinking</think> world! <think>More thinking</think>",
    expected: "Hello world!"
  },
  {
    name: "Case 5: Nested <think> tags",
    input: "Hello <think>outer <think>inner</think> thinking</think> world!",
    expected: "Hello world!"
  },
  {
    name: "Case 6: Unclosed <think> tag",
    input: "Hello world! <think>This tag is not closed",
    expected: "Hello world!"
  },
  {
    name: "Case 7: Content entirely within <think> tag",
    input: "<think>This is all thinking text that should be removed</think>",
    expected: "I'm sorry, I couldn't generate a proper response."
  },
  {
    name: "Case 8: Content entirely within unclosed <think> tag",
    input: "<think>This is all thinking text that should be removed",
    expected: "This is all thinking text that should be removed"
  },
  {
    name: "Case 9: Real-world example from Venice.ai",
    input: "<think>Okay, the user wants a short programming joke. Let me think. Programming jokes often play on common terms or puns. What's a classic one? Oh, right! The joke about loops. Like, \"Why did the programmer quit his job? He didn't get arrays.\" Wait, no, that's not loops. Maybe the infinite loop and the shampoo bottle. Let me check. \"Why do programmers always mix up Christmas and Halloween? Because Oct 31 equals Dec 25.\" That",
    expected: "Okay, the user wants a short programming joke. Let me think. Programming jokes often play on common terms or puns. What's a classic one? Oh, right! The joke about loops. Like, \"Why did the programmer quit his job? He didn't get arrays.\" Wait, no, that's not loops. Maybe the infinite loop and the shampoo bottle. Let me check. \"Why do programmers always mix up Christmas and Halloween? Because Oct 31 equals Dec 25.\" That"
  }
];

// Run tests
console.log("Testing final <think> tags filter...\n");

let passedTests = 0;
let failedTests = 0;

testCases.forEach((testCase, index) => {
  const result = removeThinkTags(testCase.input);
  const passed = result === testCase.expected;
  
  console.log(`${testCase.name}:`);
  console.log(`Input: ${testCase.input}`);
  console.log(`Expected: ${testCase.expected}`);
  console.log(`Actual: ${result}`);
  console.log(`Result: ${passed ? 'PASSED' : 'FAILED'}`);
  console.log();
  
  if (passed) {
    passedTests++;
  } else {
    failedTests++;
  }
});

console.log(`Test Summary: ${passedTests} passed, ${failedTests} failed`);

// Test the filter with a mock Venice.ai API response
const mockResponse = {
  id: "dc64c69fc0c741f3a715846f0d5e5f89",
  object: "chat.completion",
  created: 1742320456,
  model: "deepseek-r1-671b",
  choices: [
    {
      index: 0,
      message: {
        role: "assistant",
        content: "<think>Okay, the user wants a short programming joke. Let me think. Programming jokes often play on common terms or puns. What's a classic one? Oh, right! The joke about loops. Like, \"Why did the programmer quit his job? He didn't get arrays.\" Wait, no, that's not loops. Maybe the infinite loop and the shampoo bottle. Let me check. \"Why do programmers always mix up Christmas and Halloween? Because Oct 31 equals Dec 25.\" That",
        tool_calls: null
      },
      logprobs: null,
      finish_reason: "length",
      matched_stop: null
    }
  ],
  usage: {
    prompt_tokens: 19,
    total_tokens: 119,
    completion_tokens: 100,
    prompt_tokens_details: null
  }
};

console.log("\nTesting filter with mock Venice.ai API response:");
const filteredResponse = veniceApiFilter.filterResponse(mockResponse);
console.log("Original content:", mockResponse.choices[0].message.content);
console.log("Filtered content:", filteredResponse.choices[0].message.content);
