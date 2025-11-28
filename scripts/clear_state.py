import json

# Create a fresh state with position at 23.7 inches
state = {
    'usage_periods': [],
    'last_position': 23.7,
    'total_up_time': 0.0
}

# Save the new state
with open('lifter_state.json', 'w') as f:
    json.dump(state, f, indent=2)

print('Lifter state cleared and set to 23.7 inches')
print('New state:', state)
