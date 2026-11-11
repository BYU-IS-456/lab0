# Lab 0 observations

Name:

Answer each question in a few sentences, under its heading. Paste output where it helps (a trace summary line, a bad SQL query), but keep it short.

## Part 1 — What the model actually sees

### 1. How is `INV-1045 for $20,440.00` split up? What does that suggest about asking a language model to do arithmetic on invoice amounts?


### 2. `strawberry` is one token. Why might a model struggle to count the r's in it?


### 3. What is the "fixed cost" of every agent step, and where does it come from?


### 4. Did the three answers agree? Did `--temperature 0` make them identical? What does that mean for a business process that needs the same answer every time?


### 5. What did you notice when you tried other temperature values between 0 and 1, such as 0.7?


## Part 2 — Read the agent loop, then run it

### 6. In one sentence each, what happens at the numbered comments 1, 2 and 3?

1.
2.
3.

### 7. Who runs the SQL query: the model or your Python code? What exactly does the model produce instead?


### 8. How does the loop decide it's finished? Name both ways it can stop.


### 9. What is in `messages` by the third step? Why does the whole list get sent to the model every time?


### 10. In `tools.py`, where does the model get its description of each tool? What would happen if a docstring were wrong?


### Agent runs

Run each question fresh. Copy the numbers from the `===` summary line at the end of each run.

| # | Model calls | Tool calls | Input tokens | Right answer? | What happened |
|---|---|---|---|---|---|
| A |  |  |  |  |  |
| B |  |  |  |  |  |
| C |  |  |  |  |  |
| D |  |  |  |  |  |
| E |  |  |  |  |  |
| F |  |  |  |  |  |

### 11. Pick one question where the agent got the wrong answer or wrote bad SQL. What went wrong, and did it notice?


### 12. Compare the input tokens from A and B. Why does a longer task cost so much more than the number of steps alone suggests?


### 13. In D, the agent got an error back from a tool. Did it say so honestly, work around it, or make something up?


## Part 3 — The same agent in LangChain

### 14. Where did the loop go? Point to the line that replaced your 1-2-3 loop.


### 15. LangChain formats tool errors differently from your loop. Find one difference. What other decisions might a framework be making for you that you can't see?


## Part 4 — Build the policy tool

### 16. Paste the trace summary for D before and after. What changed in the agent's behavior, apart from it now having the answer?

Before:

After:


### 17. Call your tool with the topic `duplicate invoices`. How many sections come back? Why so many? What are the limits of matching on keywords?


## Part 5 — Experiments

### 18. For each experiment you ran: what you changed, what you expected, what happened.

**Experiment:**
- Changed:
- Expected:
- Happened:

**Experiment:**
- Changed:
- Expected:
- Happened:

### 19. After today, what is an agent? Use the words *model*, *tool* and *loop*.

