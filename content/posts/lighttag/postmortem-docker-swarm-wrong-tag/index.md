+++
title = "Bug Postmortem: Wrong Image Deployed on Docker Swarm"
date = 2017-12-03T00:00:00Z
draft = false
description = "A production postmortem about a Docker Swarm deployment that served one customer the wrong frontend version."

[social]
image = "social.webp"
image_alt = "Archive cover for Bug Postmortem: Wrong Image Deployed on Docker Swarm."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/postmortem-docker-swarm-wrong-tag/"
+++
On Thursday June 7th 2018 a new customer emailed us reporting that they were unable to submit the work they'd done on our platform. The cause of this error was the deployment of an outdated version of our frontend. Other customer sites and customers who use our on-premise offering were not affected.

LightTag is a tool to make the work of labeling text easy. Being unable to submit work to our servers is unacceptable. In this postmortem we will examine what went wrong at both a technical and process level and explain the steps we've taken to prevent this from happening in the future.

We're very inspired by other postmortems we've seen, notably [GitLab's postmortem of their database outage](https://about.gitlab.com/2017/02/10/postmortem-of-database-outage-of-january-31/). We hope that by being transparent about our errors and the steps we are taking to mitigate them we can continuously improve and maintain the trust that our customers put in us and our systems.

## tl;dr

Our frontend application is served from a container that runs on a [Docker Swarm](https://docs.docker.com/engine/swarm/) cluster. When we onboarded the customer who reported the issue we mistakenly deployed the frontend image tagged *latest* (instead of the image tagged with the highest semantic version) from our container repository.[When deploying a stack](https://docs.docker.com/engine/swarm/stack-deploy/),  Docker Swarm will not pull an image onto a host if that image already exists on the host. Thus when we deployed our customers stack they ran an outdated frontend, since an image tagged *latest* already existed on the host.

The technical resolution for this issue is deploying images based on their [semantic version](https://semver.org/) tag. We knew this before the issue occurred and so realize that this issue is caused by a gap in process, not in technology. Our deployment process did not have sufficient controls and monitoring over precisely which image is deployed.

## Our Infrastructure

LightTag provides a text annotation platform as either a hosted solution (SaaS) or on-premise installation. In order to keep complexity down our SaaS deployment is (almost) equivalent to our on-premise deployment. In particular the components that make up LightTag, such as a database, backend server and machine learning processes are each run inside of a container orchestrated by Docker Swarm.

 In our hosted offering, each customer is allocated their own set of containers ([a stack](https://docs.docker.com/engine/swarm/stack-deploy/) in the Docker Swarm parlance) which lets us offer our customers full isolation while remaining cost efficient. One of the components that runs in it's own container is our frontend ReactJS application which is statically built and served by our proxy server.

 Previously we deployed each new customer in a manual process and we recently migrated to a fully automated self service on-boarding process, the relevant part of which defines and deploys a stack of containers into our Swarm cluster. The customer that reported the error was the first to go through this automated deployment process, hence why they were the only one to experience this issue.

## Root Cause

 We've been aware of Docker Swarm's behavior (not pulling an image if it exists on the host) for some time. During our days of manual deployment this was a frustrating point which entailed an extra step, updating a service and [forcing it to pull](https://stackoverflow.com/a/45963442/3860898) after deployment. While frustrating, it was on our deployment checklist and so was not missed.

 To generally improve our engineering practices and particularly to get more visibility into what we are deploying, we embraced semantic versioning. In particular we adopted the [Semantic Release](https://github.com/go-semantic-release/semantic-release) library as part of our CI/CD pipeline. This library calculates the latest SemVer based on commit messages, and we tag each new image with the calculated semantic version.

Our deployment service takes advantage of this, querying our container repository ([example](https://gist.github.com/talolard/5fde6e5c036e6fffbf588ddbe0100410)) and selecting the image:tag with the highest semantic version which it deploys to the customers stack. This is done for each of the containers in a customers stack.

Technically, this issue occurred because a bug in our deployment script did not check for the frontend's highest semantic version tag, instead it deployed the latest tag, a relic from when we prototyped the deployment service.

## Gaps in Process

 A better internal process would have detected this error. Here are the gaps in our process that we've recognized as facilitating this error

* We did not have an integration test in place that checked the tag of the image in the generated docker-compose file (from which we deploy a Stack onto Swarm)
* Our monitoring tools were not set up to check which tag is running on a particular container. Thus even though we could see that the customers container was running the *latest* tag, we assumed everything was ok

## Steps we are taking

1. We're setting our monitoring tools to validate that the tag of each container matches the highest semantic version tag in the images repository.
2. We're adding the missing tests to our deployment codebase
3. We've add a feature to the front end application which, in case of error, serializes and downloads any work done onto the users local machine. This will allow our users to recover their work if an error occurs.

If you think there are additional measures we can take to prevent incidents like this please let us know
