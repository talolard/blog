+++
title = 'I Needed One Obscure Vision Model. Modal Made It Everyone Else’s Problem.'
date = 2026-04-08T01:10:00+02:00
draft = false
tags = ['agents', 'computer-vision', 'inference', 'mlops', 'modal', 'diffusers', 'torch']
description = 'How I vibe-coded an obscure Diffusers-adjacent vision model into a serverless GPU endpoint on Modal, then optimized cold starts and inference latency so it stopped dictating my UX.'

[social]
image = 'social.png'
image_alt = 'Social cover for a post about deploying an obscure vision model on Modal and optimizing cold starts, inference latency, and scale-to-zero behavior.'

[share]
disable = false
+++

I am building an agent that measures rooms from photos.

Not in the cool, LiDAR, "Apple already solved this" way. In the embarrassing way. A human takes photos of a room, and the agent tries to infer enough geometry to be useful.

The problem is not my ambition. It's my ability to measure.

I needed per-pixel surface normals. The kind of thing you can get from an obscure vision model that lives on GitHub, is wired into Diffusers, and ships a `torch.hub.load(...)` entrypoint like a trap.

The model I wanted was StableNormal Turbo:

```python
predictor = torch.hub.load(
    "Stable-X/StableNormal",
    "StableNormal_turbo",
    trust_repo=True,
)
```

That is a *great* one-liner.

It is also not an endpoint, not a budget, not a security posture, and not a user experience.

This post is the story of how I turned that one-liner into a serverless GPU service on Modal, and then tuned it until it stopped dictating the pace of my development and the shape of my UX.

This is not production. But it is *fast enough* that I can build like it is.

## The real spec

My spec was not "deploy StableNormal." My spec was: someone else hosts the GPU, I pay per use, it scales to zero, and it's fast enough that it doesn't become a product constraint.

Scale-to-zero matters because my traffic pattern is: me procrastinating, then me overfitting a pipeline for three hours.

Speed matters because latency becomes product scope. Slow inference turns into fewer user interactions, fewer iterations, fewer features, and more "I'll do it tomorrow."

And yes, I wanted it locked down. Running remote model code behind a public endpoint is how you end up with a blog post called "How I accidentally deployed my threat model."

Modal is basically designed for this: ship a container, run it on a GPU, pay per second, scale down aggressively. Great.

## One concept before we touch code: cold starts are a tax you choose

If you configure scale-to-zero, you are choosing to pay cold start sometimes.

That's not bad. It's honest. It just means you need to stop talking about "latency" like it's one number.

There are two numbers:

Cold latency is container start, imports, model init, first inference, and whatever compilation/JIT happens on that first call. Warm latency is the actual inference path when the container is already running.

If you're building an internal tool, warm latency is what controls your workflow. Cold latency is what controls how annoying it feels when you come back after coffee.

I cared about both.

## Diffusers models are slow on purpose

Most Diffusers pipelines are slow because they are iterative.

They start from noise and repeatedly denoise. You pick the number of steps. Steps buy you quality at the cost of time.

StableNormal Turbo is "turbo" because it cuts work, but it still runs a non-trivial pipeline (ControlNet-ish plumbing, U-Net forward, VAE decode, pre/post).

So I treated it like a real inference service, not a toy.

## The thinnest Modal wrapper that works

The first goal was boring: make it work. The second goal was more boring: make the request/response shape sane.

I made two opinionated choices immediately:

1. **No URL fetching in the hot path**. The request is raw image bytes. If the client wants to fetch a URL, that is their problem.
2. **No base64 JSON responses**. The response is raw PNG bytes. Life is too short.

On Modal, the shape that worked best for this was a class with an `@enter` hook (load once per container) and a method (run per request).

I am not dumping the whole file here, but the important idea is: load once, run many.

## The optimization loop (a.k.a. vibe-coding infra)

This part surprised me: I did not really "engineer" this service.

I mostly prompted an AI to:

change the request shape, add caching, try knobs, run benchmarks, and write down results.

Modal was the substrate. The assistant was the sweaty intern. I was the product manager with a stopwatch.

If you are allergic to the phrase "vibe coding", I get it. I am too. But this is what it looked like: I pointed at pain, the assistant changed code, we measured, we kept what helped, and we threw away what didn't.

The key is that we wrote down everything in a logbook so this didn't turn into folklore.

## What actually moved the needle

Below is the short version of the experiments. The longer version is: measure cold and warm separately, and don't trust your intuition.

### The scoreboard (numbers, not vibes)

These are real timings from sequential requests. They vary based on whether the container actually stayed warm, but the pattern was stable:

| Stage | Cold-ish | Warm |
| --- | ---: | ---: |
| Early version (public HTTP, heavier request/response overhead) | ~66–130s | ~2.3s |
| After caching weights + fixing shapes | ~46s | ~2.3s |
| After moving to L40S | ~16s | ~1.3–1.6s |
| After enforcing strict execution timeouts + scale-to-zero friendliness | ~15–17s | ~2.0s @ 768 |
| Same, but lower internal resolution | n/a | ~1.1s @ 512 |

If you only take one lesson from that table, make it this: **resolution is a product knob**.

### Cost (the part everyone hand-waves)

Modal bills by time. So the cost per request is basically:

`cost = seconds * $/sec`

At the time of writing, the per-second prices I saw in the Modal UI were roughly:

- T4: `$0.000164 / sec`
- L40S: `$0.000542 / sec`

So yes, L40S costs more per second. But if you're running scale-to-zero, **you are often paying for cold-ish requests**, and that's where the speedup can win on cost too.

Example: one of my early cold-ish T4 requests was ~130 seconds. That's about `$0.021` of GPU time. The L40S cold-ish request later was ~16 seconds, about `$0.0087`. Cheaper, even though the GPU is pricier per second.

Warm requests are a different story. If you keep containers warm and do lots of steady traffic, the math can flip (because L40S isn't 3x faster than T4 for this pipeline). The point is: you can't guess. You measure, then you pick.

### 1. Fix the API shape first (boring wins)

First, I made the API shape boring: bytes in, bytes out. Raw uploaded image bytes in the request body, raw `image/png` bytes out. It didn't magically drop warm latency, but it removed failure modes and overhead from the hot path, and made the call site dramatically simpler.

Then I exposed the real knobs: `resolution` and `num_inference_steps`. Now performance is tunable without redeploys, and the product can decide between "fast" and "quality" without begging infra for a favor.

### 2. Remove downloads from cold start (Modal Volumes)

StableNormal Turbo pulls weights. Pulling weights at cold start is how you discover the meaning of life while watching a progress bar.

Putting weights on a Modal Volume moved that download out of the critical path after the first run. This was the single biggest cold-start win. I didn't "optimize the model"; I just stopped redownloading it.

Impact: cold start dropped dramatically after priming. This was the first change that felt like "oh, this is a service now."

### 3. Stop shape chaos (resolution buckets)

The model internally resizes to a working resolution. Letting callers send arbitrary values is a trap, especially once you start thinking about compilation and caching.

So I bucketed to a few fixed internal sizes:
`512`, `768` (default), and `1024`.

Impact: more predictable performance and a simpler mental model. Also a prerequisite for any serious compile/caching story.

### 4. Upgrade the GPU (sometimes the best optimization is credit card)

On a T4, the warm path was fine but not delightful.

Moving to an L40S made the warm path feel like a normal RPC, and made the cold path less offensive.

Impact (ballpark): warm latency roughly halved. Cold latency dropped by ~3x versus my worst early runs.

### 5. `torch.compile`: powerful, expensive, not always worth it

If you've read the PyTorch/Diffusers optimization docs, you've seen the promise: compile the hot modules, get faster inference.

In practice, for this service pattern:

- Compilation cost tends to show up on first inference (which is exactly when scale-to-zero already hurts).
- It can be sensitive to shapes, which is why bucketing matters.
- Even with cache directories persisted, "compile it in production as the default online path" was not operationally sane for me.

My conclusion: `torch.compile` is worth it when you have stable shapes and enough warm traffic that the first-run penalty amortizes. For my dev workflow, it was a lever I kept, but not one I enabled blindly.

## The benchmark that mattered for UX

The question I cared about was: "If I’m building an agent UI, how long does a normal map take?"

With aggressive scale-to-zero and strict timeouts, I got:

- **Cold-ish request at `768`**: ~15–17s
- **Warm requests at `768`**: ~2.0s
- **Warm requests at `512`**: ~1.1s

That last line is the one that changed my behavior.

At ~1 second, I build an interactive loop. I can afford to run normals repeatedly while refining other parts of the pipeline. I stop hoarding model calls like they are a scarce resource.

And because it scales to zero, it costs me basically nothing when I’m not using it, which is most of the time.

## Security: stop exposing remote code as a public web endpoint

StableNormal Turbo uses remote code. Even if you trust the repo, you should treat that as a privileged operation.

So the service is not a public endpoint anymore. It is an authenticated Modal method call from a client that has Modal credentials.

That is not "enterprise security." It is just: please do not leave sharp knives on the sidewalk.

The call site ends up looking like this:

```python
import modal

StableNormalService = modal.Cls.from_name(
    "modalsetup-stablenormal",
    "StableNormalService",
)
service = StableNormalService()

with open("room.jpg", "rb") as f:
    normals_png = service.predict.remote(
        f.read(),
        resolution=768,
        num_inference_steps=None,
    )
```

## Takeaways (for your next obscure model)

- Start by making the request/response shape boring. Bytes in, bytes out.
- Separate cold from warm and decide which one you care about.
- Persist weights. Then consider persisting compilation caches.
- Bucket shapes. Shape chaos destroys predictability.
- Use `resolution` as a product knob. It is the cleanest latency lever you have.
- Treat `torch.compile` as a tradeoff, not a checkbox.
- If you need to ship fast, sometimes the best optimization is a better GPU.

## What I’m doing next

Now that I have normals, I can go back to the real project: the agent.

The normals are not the product. They’re just one perception primitive that buys me geometric structure.

But they do set the tempo.

And tempo is product.
