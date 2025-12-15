+++
title = 'Five Practical Lessons for Serving Models with Triton Inference Server'
date = 2025-12-15T10:00:00+02:00
draft = true
tags = ['machine-learning', 'mlops', 'inference', 'triton']
+++

Triton Inference Server has become a popular choice for production model serving, but deploying it effectively requires understanding its quirks and capabilities. After working with Triton in production environments, I've distilled five practical lessons that can save you time and headaches.

## Choose the Right Serving Layer

Not all models belong on Triton. **Use vLLM for generative models; use Triton for more traditional inference workloads.**

LLM's are all the rage these days, and Triton has an integration with Tensorrt-LLM, Nvidia's solution for LLM serving.
Triton also has a "vLLM" backend, and so it seems at first intuitive that Triton is built for smooth sailing with LLM's as well as classical models.

My own experience has been that Triton doesn't add much over a "raw" vllm experience. That's because LLM's and generative workloads are different enough to not benefit from the great features that Triton has.

* **Dynamic Batching -> Continuous Batching** Triton excels at dynamically batching requests , so that they all get processed at once. LLM's need continuous batching, such that as soon as one item in a batch finishes generating, we "hot-swap" in the next item. This "can-be-done" in Triton, e.g. one can access the continuous batching features of the vllm backend, but it's not easy or obvious.

* **Model Packing -> Model Sharding** Triton makes it easy to pack multiple models on a single GPU, to greatly increase hardware utilization and throughput. However, LLM's being as large as they are, a very modest LLM will take a whole GPU, and a run-of-the-mill LLM will require sharding across GPUs if not nodes. Triton doesn't preclude sharding, but wasn't design with it in mind and adds no benefits or quality of life.

* **Request Caching -> Prefix Caching** Caching request-response pairs is a simple and effective way to dramatically increase throughput and lower global latency. But generative workloads require a different form of caching, namely caching intermediate computations such as the KV-cache, keyed according to a common prefix. For example, the common prefix of our codebase might be cached, so that developers don't need to wait for that context to be processed on every request. This caching style is worlds apart from the built in caching in Triton.

My own experience has been that it is dramatically simpler to spin up Vllm with the model I want directly, and immediatly benefit from it's continuous batching, model sharding and prefix caching, rather than using triton over vllm or tensorrt-llm and trying to beat the triton config files into submission.

## Protect Latency with Server Side Timeouts

Triton's killer feature is dynamic batching, where it buffers incoming requests in a queue for a user specfieied amount of time, and then processes them in batch. This is a kiler feature, because not only does it make it easy to utilize the hardware we pay for, it greatly simplifies the logic and code in calling applications, who no longer need to concern themselves with batching, and the associated book keeping and shape shifting.
There is a catch, that by default, the queue triton maintains will never evict a request, unless the user configures the max queue duration. It can thus happen that during high load, triton will get backed up, and while a caller might time out and ignore the request.
If we don't set server side timeouts with `max_queue_delay_microseconds`, the request will remain in the queue and block any subsequent requsts, making your model process requests your client has forgotten about, while making your client wait for the backlog to be cleared.
This problem is exasperbated in particular by the Python backend. Whereas other backends will automatically check if a request was cancelled (for example if the client dropped a minute ago and triton detected it) , the python backend leaves it to us to check for cacnelled requests and handle (or ignore) them ourselves.

## Keep Client Libraries Minimal

When we configure model's in triton, we give names to it's input and output tensors, and define their shapes. Triton reads to config to create a JIT protobuff, and during inference, someone needs to know exactly what each model is named, what it's tensors are called and what type they are.
I've found it very helpful to provide a client library that handles that logic for end users, so that their experience of using triton amounts to `output = triton.infer(input)` . However, where there is a client library, there can be temptation to solve problems end users have while using the client library. For example, retry logic. We did indeed experiment with wrapping calls inside the client with a retry library like `tenacity` but encountered a number of painful edge cases. Notably, retries would occour when Triton didn't respond in time due to load, and / or invalid requsests. Both situations can easily amplify a high load moment and end up ddosing your server.
Instead, I'd recomend having the calling application implement retry logic near it's own call site, and with the specific context of the calls it may have. This also has the advantage of making logging and tracing a deal easier.

## Leverage Triton's built in Cache

Triton has a built in request response cache, that will spare your GPU precious cycles if a rouge client is sending duplicate requests.
This suggestion isn't a steadfast rule, but I think it's particularly pertinent in the cloud, where a gpu enabled node will come with an abundance of RAM that you won't be using. If you do notice a few extra gigabytes of unused RAM (AWS's g4dn.xlarge comes with 16), try putting it on your models and tracking the cache hit rate and queue depth, to see if you've 1) Solved a problem and 2) Found a client who is stressing the system more than is neeed

## Clients should use the Threadpool executor for parallelization, not bacthing or asyncio

I recently learned that opening a socket releases the GIL in python, meaning that an easy way for your clients to send
parallel requests is with
```python
def infer(inputs):
    return model_client.infer(
        inputs=inputs,
)

with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(infer, batch_of_requests))
```

Any logic in the `infer` method will block, and add a slight jitter, which is a "good thing". This method allows
1) relieving the client of batching logic (it relies on Triton's dynamic batcher)
2) Facilitating batching across multiple concurrent clients


## Conclusion

<!-- TODO:
- Summarize the five lessons
- Emphasize the importance of matching tools to workloads
- Mention resources for further reading
- Call to action or next steps
-->
