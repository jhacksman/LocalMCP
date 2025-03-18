// Improved function to remove <think> tags from content
function removeThinkTags(content) {
  if (!content) return "";
  
  // First, handle properly closed <think> tags
  let cleanedContent = content.replace(/<think>[\s\S]*?<\/think>/g, '');
  
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
    name: "Case 5: Nested <think> tags (not properly handled by regex)",
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
console.log("Testing improved <think> tags filter...\n");

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
