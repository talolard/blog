+++
title = "Database Multi-Tenancy for SaaS"
date = 2020-12-19T00:00:00Z
draft = false
description = "A practical account of isolating tenant data in a SaaS application with separate PostgreSQL schemas."

[social]
image = "social.webp"
image_alt = "Archive cover for Database Multi-Tenancy for SaaS."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/database-multi-tenancy/"
+++
![Database Multi-Tenancy Architecture](db-diagram.webp)

At LightTag, we do database multi-tenancy with Django and Postgres. That means we run a SaaS with multiple customers, and each customer's data lives in their own isolated database.

In this post, I'll tell you why we chose database multi-tenancy, what it took to make it work, as well as what we gained, and what we lost.

## Will this article help me ?

Maybe. We're a small bootstrapped company whose product and architecture make extensive use of the database and have strong requirements around tenant isolation. Our multi-tenancy story has worked well for us, and if you're requirements are similar this might be useful.

## The Three Multi-Tenancy Models

You have an application; it has data in the database. You also have multiple customers (tenants). The way the relationships between tenant,application and database are managed is the multi-tenancy model. There are three multi-tenancy models: Database, Schema, and Table.

In **Database multi-tenancy**, the application connects to a database and gets data while the tenancy logic is delegated to the ops layer. In an exemplary implementation, the application has no concept of tenants.

In **Schema multi-tenancy**, your application connects to a database once and has some logic to choosing which schema to connect to when serving a particular tenant.

In **Table multi-tenancy**, every row in every table is associated with a given tenant. The application doesn't need to worry about which schema or database it is connecting to. Instead, the business logic also maintains the tenancy logic.

## The Cost Of Table Multi-Tenancy

![Table Multi-Tenancy Architecture](table-diagram1.webp)

## Avoiding Table Multi Tenancy Makes Disasters Impossible

Our business deals with customer data. If we ever mistakenly shared one customer's data with another, it would be a disaster for them and us. Table multi-tenancy means the tenant logic lives in the application layer and thus offers many opportunities to make mistakes and leak data.

By removing the tenancy logic from the application layer those mistakes become impossible. Making disasters impossible is a compelling reason to avoid table multi-tenancy.

## Table Multi Tenancy Slows Down Engineering

When tenancy logic lives in the application layer, every change needs to take that logic into account. We deemed a the cost of a mistake in tenancy logic to be very high, and so would have to implement a defensive engineering process to allow application level tenancy. This slows down the development cycle.

By moving tenancy out of the application layer, we reduce the  cognitive load and process complexity of our engineering team, making them more productive.

## Schema Multi-Tenancy

![Schema Multi-Tenancy Diagram](schema-diagram.webp)
Schema multi-tenancy is both compelling and popular. The tenancy logic still lives in the application, deciding which schema to access data from.

The Schema routing logic can be encapsulated in a small and well-guarded router. Isolating the connectivity logic solves most of the problems we had with table multi-tenancy while being operationally simpler than database multi-tenancy.

## Database Multi-Tenancy

![Database Multi-Tenancy Architecture](db-diagram.webp)

In Database multi-tenancy, each tenant lives in a separate database. The database could be a separate server or merely a different database within the same Postgres server. In hindsight, that flexibility is one of the most compelling reasons to do database multi-tenancy.

## Advantages of database multi-tenancy

### Peace Of Mind

The most significant advantage of database multi-tenancy is the peace of mind. It's simply impossible for one tenant to see another tenant's data due to a bug in the application layer.

As we've grown, we've come to appreciate another advantage of database multi-tenancy, the ability to move customers to different physical machines.

## Database Multi-Tenancy Solves The Noisy Neighbor Problem

SaaS customers follow the 80/20 rule: 20% of your customers will provide 80% of your infrastructure problems and revenue.

We've had several instances of customers scaling to our application design or hardware resource limits. This impacts both the scaled customer, and everyone else because they share constrained resources.

With database multi-tenancy, we've been able to move a particular customer to a dedicated machine, temporarily solving their problem, eliminating noisy neighbor issues for our other customers, and giving us breathing room to address the root cause.

In that sense database multi-tenancy has been a business advantage, allowing us to easily respond to scaling issues and thus retain and expand customer accounts.

## Database Multi-Tenancy Makes On-Prem and Compliance Easy

Database multi-tenancy enforces constraints around the separation of concerns that can be very annoying at times. However, that has also proven to be an advantage.

We've been able to accommodate customers who needed deployments in an EU-based cloud as well as sell our software on-premise, both with minimal modification to our overall engineering posture.

Being able to sell more, sell easily and particularly to sell on-prem, is a significant upside of database multi-tenancy. We had anticipated our customers would have these demands ahead of building and which made betting on database multi-tenancy easier, and in retrospect those bets paid off.

## Database Multi-Tenancy Drawbacks

Everything in engineering is a trade off. When you choose database multi-tenancy you get the advantages we described above, but you pay in spades with operational complexity.

While everything is solvable with engineering, engineering takes time and money, and database multi-tenancy demands those investments upfront.

## High Upfront Investment In Ops

At the ops layer, we maintain an application instance (a process) for each active tenant. By doing so, we keep the application utterly unaware of the multi-tenant environment. Instead, the ops and networking layers are wholly responsible for tenancy logic.

Running an application instance for each tenant is easy at first, but we found that we needed significant resources and expertise to operate such an architecture as we scaled.

We started to scale around when my son was born, and I have a beloved picture of him sleeping on my lap as I'm restoring a docker swarm cluster that ran out of IP addresses.
![Fixing A Broken Container](baby.webp)

## Database Multi-Tenancy Makes Analytics Hard

As our product matured and we started acquiring customers, we transitioned from building a product to building a SaaS business.

Database multi-tenancy made that harder because each customer was isolated. Answering simple questions like "Who are the top ten most engaged customers" became an ETL challenge because we needed to collect each customer engagement data from each isolated database.

Compared to table multi-tenancy, doing analytics in database multi-tenancy is significantly more challenging because you can't do ad-hoc BI queries across your tenants. Schema multi-tenancy is also simpler because it allows access to each tenant within the same connection, whereas database multi-tenancy requires "ops" for any cross tenant query. After all, the database connection sees a single tenant at a time.

ETL is solvable with engineering, but that's a bad thing. Engineering takes time and resources, which means that the cost of an ad-hoc query or a marketing experiment is high, and that slows down the business.

## Would We Choose Database Multi-Tenancy Again ?

Yes!

In hindsight, the advantages database multi-tenancy offered us significantly outweighed the costs. There are classes of problems that we don't have and the infrastructure flexibility is very aligned with our business model.

I made the this decision and did the first few passes of implementation. If I had to do it again, I'd do two things differently. First, I'd spend more time thinking about the control plane and analytics infrastructure and designing for that upfront. Second, I'd recognize that this is complicated and hire an expert to hold our hands through the design.

Good luck on your own multi-tenancy adventure.
