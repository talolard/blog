+++
title = 'Engineering Agents is really UX Engineering'
date = 2026-03-09T02:11:00+01:00
draft = false
description = 'Building trustworthy agents is mostly a UX and state-sync problem, not just a framework or prompting problem.'

[social]
image = 'social.png'
image_alt = 'Social cover for a post about agent trust, memory design, and why engineering decisions become UX outcomes.'

[share]
disable = false
+++

Over the weekend I built an AI agent. I thought this was an engineering problem, but I now think it is a user experience problem.

In regular software, we solve engineering problems with UX. If a page loads slowly, we show a spinner so the user feels like something is happening.

In agentic software, we create UX problems with engineering decisions.

If we take some data out of the chat history, but hint at that data in the UI, the user will think the agent is dumb and will stop trusting it. If we do not manage the agent’s “memory” carefully, the user will feel like they are talking to a different person every time. User trust collapses when the UI, and the data informing it, diverge from the agent’s memory.

But I am getting ahead of myself.

We rent an apartment in Berlin, and as the kids grow we need to rearrange their rooms. I hate this task because I am so bad at it.

I cannot measure. I cannot design. Since it is a rental, it is not worth spending big bucks. And the worst part is searching for furniture that fits exactly, one slow click at a time.

So I built an agent that measures, makes floor plans, figures out what is wrong with our layout, checks what fits, and orders from the catalog.

In order to use it, I just need to trust it.

## What's inside
Two themes:
- **Choosing tools for building Agents**:
  Looking back on my research and choices, should you use an agent framework (Yes!)? Which one (They're not really differentiated)? What matters (a chat UI from day 1 + recording of every interaction)?
- **Engineering Agents is user experience design**:
  Users need to trust their agents. The wrong engineering decisions will make the agent feel dumb, erode user trust, and kill your KPIs, company, and reputation.

## Context, State, and Memory

These are confusing words that are confusingly used together, so let me define them the way I am thinking about them.
- Context: the text the agent is currently working with
- Memory: more text the agent can retrieve or “remember” if it needs to
- State: the rest of the data in the application that influences the user’s perception of what is going on. The current floor plan, the progress bar, whether the agent is waiting for input, and so on.

When I use a coding assistant, memory feels a lot like context, because a coding agent running on your machine can just use the file system as memory. You and Claude operate on a shared data plane: the file system. If the agent writes a class or creates a folder, that change creates a persistent artifact that both of you can see.

In my furniture planner, there is no such shared file system.

The agent lives inside a webapp that does other things. The user and the agent are collaborating through chat to create assets—like a floor plan—that need to persist outside the chat stream. So I had to build a persistence layer that keeps both the application state and the conversational memory alive, and keeps them in sync.

That sounds technical, but it is really a product problem.

First, there is the question of continuity. If I start a new conversation, should the agent remember the floor plan? Probably. But what about the commentary around it?

Suppose the user previously said: “My wall is 350x400 and the unusual height makes me feel cold and uncomfortable.”

Persistence will happily store the wall dimensions, so we have them in the app. But the user’s remark about the unusual height, and how it feels, is easy to lose, as those typically only get stored in the message history. 
Next time we load the project, the user will think it is obvious that this wall is part of the problem. The agent will likely just accept the dimensions as facts and fail to understand the emotional context that should steer the conversation. The user will feel like the agent is not keeping track of what it's supposed to remember, and that it is just a dumb tool. That is a trust problem.

Second, there is the synchronization problem. What does the UI think is happening, versus what the agent thinks is happening?

If the UI renders a floor plan, we naturally assume the agent is aware of it. But if the user tweaks the plan in the UI, does the agent know? Is the agent’s context synchronized with the database state? Is what the user sees the same thing the agent is reasoning from?


## Choosing Tools for Building Agents

I started this project thinking the big technical question would be: what framework should I use?

I now think that question matters less than I expected. What mattered the most is the ease of integration with UI. Whatever form your agent takes, it's very helpful to interact with it in that form and experience it as the user would. My agent had a lot of media to navigate and display, so a web page with a chat made sense. Having that out of the box from my framework (Pydantic) was a huge help.

As an example, what is the user experience while my agent searches the Ikea catalog? Do we just display a spinner indefinetly? Of course not! There is a standard UI pattern for "tool calls", and I am thrilled to not have rediscovered or reimplemented it myself. I used CopilotKit's agent UI frameowkr and it made life easy. 


## Multiple Agents == Multiple Personalities == Hard to Trust

Once I had the UI and the state problems in view, another issue became obvious: multiple agents.

In my workflow, I want different kinds of agent behavior at different times:
- one that specializes in measurement
- one that specializes in understanding needs
- one that matches those needs against the design catalog
- one that does constrained optimization to make sure the solution is actually feasible

From an engineering perspective, it is very tempting to make these isolated components: multiple agents that don’t share state. One feeds the next. It’s easier to reason about and easier to debug.

The alternative is a single agent that knows everything, remembers everything, and does everything. That’s harder to engineer, but it has one huge advantage: it feels like one coherent actor from the user’s perspective.

Generating the floor plan is not a one-shot transformation. It is a conversation. The agent asks for information, draws something, the user says “no, the door is on the other side,” or “you forgot the window,” or “there is a couch here.” The agent refines, asks follow-up questions, interprets corrections, and keeps going until the user is satisfied.

For that sub-workflow, I don’t really want the whole rest of the system involved. I don’t want every tool, every piece of state, every message, all crammed into that one loop. I just want it to stay in that conversation until the floor plan is good enough.

But here’s the trap: when that separation shows up to the user as “forgetting,” it destroys trust.

If the floor-planning agent doesn’t remember something the user already said earlier in the broader chat, it looks dumb. The user does not think “ah yes, I see I have crossed a subsystem boundary.” They think the agent forgot.

This is why I say multiple agents can feel like multiple personalities. Even if the decomposition is elegant internally, it can feel like talking to someone with selective amnesia.

Right now, this is a me-facing tool, so I’m not overly worried. But as soon as the user is meant to trust the system directly, this becomes a major issue.

## Prompt Management and Evals

Another place where the “one coherent actor” illusion breaks is prompting.

Once the high-level agentic workflow is there, the prompt(s) are what drive nuance of behaviour. 

For example, I added a semantic search layer over the product catalog.

I prompted the agent to run 5 or 6 variations of a concept. So instead of searching only for “plants,” it might search for “low-light plants,” “shadow-loving greenery,” “bathroom plants,” and so on.

That diversity mattered a lot. It forced the agent to explore the catalog instead of lazily grabbing the first plausible results.

Then one day, that part of the prompt disappeared.

The code was fine. The system still worked. But the quality dropped hard, because the agent stopped searching broadly and started doing the lazy obvious thing.

That kind of regression is hard to catch. “Generate several related but distinct search queries” is not a crisp unit-testable behavior. It is a qualitative behavior. The code can be perfectly correct while the intelligence degrades.

That is why prompt management matters. I want to know the state of the prompt. I want to version it. I want to understand how one piece of prompting affects one behavior. Otherwise the whole system turns into a clot of instructions that is impossible to reason about.

Modern coding assistants are a good analogy. They have a system prompt, then extra context files, then tool definitions that add more instructions. Prompting is no longer one blob. It is compositional. That same complexity exists in the agents we build ourselves.

## Defining Behavior: User stories and Capabilities over Specs

In normal software work, I have had the best luck with agents when I give them detailed technical specs. The spec says how to test, how to implement, what constraints matter, what patterns to follow.
But when engineering agents, where engineering errors erode *user trust* in the agent, then user stories and agent capabilities replace specs as the cornerstone of planning and design.

Agent capabilities might sound like `Skills.md`, but it's not the same. A skill spec says "here is how to do x and what you need to do it". Describing a capability is more like saying "I want you to solve this problem" and expecting the agent to fill in the blanks.

For example, I might define a capability like Estimate Room Measurements from Photos. I want the agent to ask for photos, combine them, and infer dimensions of the room and the objects in it. I do not necessarily want to start by prescribing: use semantic segmentation, depth estimation, plane detection, vanishing points, and so on.

Partly that is because I was working in areas where I did not know enough to write the right low-level spec. Computer vision, frontend, etc.

But partly it is because the agent is a user-facing product. The important thing is not the internal recipe. The important thing is the behavior: what it helps the user accomplish, how it asks questions, what it does when it is uncertain, and what result it is trying to produce. What do we need to validate between releases? Not the "how" of how it reaches an answer but the "what", what was the answer and was it right?



## The Happy Path Strategy

One practical way I managed the chaos of user stories for agents was by defining a very rigorous happy path.

This is a closed workflow. The user is trying to reorganize a room. That means most possible things they could say are actually out of scope.

The happy path looks roughly like this:

1. Discovery: what is the user trying to do?
2. Solicitation: collect constraints, preferences, and photos.
3. Construction: build the floor plan.
4. Refinement: solve problems and swap furniture.

Everything else is basically exception handling.

If the user asks about God, uploads a picture of a cat, or says “stop” halfway through a measurement flow, those are deviations from the intended flow and need explicit handling.

This helped me a lot because you cannot really unit test the magic. But you can define the conversation that should contain it.

You can define what “stop” means during measurement versus during shopping. You can say that if a photo is clearly not a room, the agent should reject it politely. In older software, I would have needed to build a dedicated detector for that. Here I can rely on the model to identify the image, and focus my specification on the behavior.

A traditional spec might define the ImageError class. A conversational spec defines how the agent politely explains that a cat is not a bedroom.

For these systems, that conversational rigor is the safety net.

## Summary

Building this agent taught me a few things.

Framework choice matters, but less than I expected. Graphs are useful once the workflow is real, but they are not what makes the product feel intelligent.

A basic chat UI matters much more than I expected, because it lets you debug the system in the same mode that the user will experience it.

Prompt management matters because behavior regresses in subtle ways, and code correctness does not protect you from that.

Multiple agents are attractive architecturally, but from the user’s point of view they risk becoming multiple personalities.

And the hardest problem, really, is state.

A web agent is not living in the file system with you. It is living in an application, with a database, a UI, and a conversation. The product only works if those things stay synchronized closely enough that the user feels the agent is living in the same reality they are.

That is what trust is, in this kind of software.
