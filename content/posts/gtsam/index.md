+++
title = 'Engineers Guide to GTSAM and Slam'
date = 2024-03-15T09:41:38+01:00
draft = true
+++

In the course of my work on an agent that helps measure rooms, I needed a way
to estimate how uncertain or wrong the agent was. I ended up choosing a library
called gtsam, I'll say why in a second.
I learned a lot, spending a fair deal of elbow grease on it, and want to share
some learnings for the next person that comes along. So I gues we should structure this
0. Me and my use case
1. What is gtsam
2. Why did I pick gtsam over other things
3. How to learn gtsam
4. Rough edges
5. Highlights

## Me and my use case
I am building an agent to buy bundles of furniture for a room. As part of that
I want to get precise estimates of the room dimensions, without burdening the user.
Sure, but any AI model will tell me it is precise, even when it is very wrong, and
so I want ways to estimate my precision, or my uncertainty in the precision of my estimates.

The way this works in practice is that the user gives me a picture, I find stuff in it
like a door and I believe that doors are more or less 80 cm wide and 200 cm tall .
If I can spot a few things like that, I can "reconstruct the scene" e.g. where the camera was
and then the scale of all the things I care about.
The issue being that this is all aproximate and error pronme, is that really a door,
is that precise pixel a door or is it the casing, is the camera aligned with horizon or tilted,
is the photographer a short child or tall adult (which defines the camera height) etc,
did they use a new camera or an old phone with a bug in the zoom logic ?

And so


from this list of pain we can figure out what kind of solution I was looking for,
something that handles "uncertain beliefs", that has notions of geometry and camera's
and "prohjective geometry" (how a camera projects the 3d world to a 2d photo) and
naturally has these things connect (e.g. if I have two uncertain points in a photo and
some belief on the camera , I can connect all of those and get a better total estimate on all of them )

And, I want it to be fast, because there is only so long a user will wait, and I'd rather burn that
budget elsewhere .

## What is gtsam: Three definitions
1. Tal's definition: Gtsam is a library for fast probabalistic geometry that supports discrete and continuous data
2. gtsam's's Github: "GTSAM is a C++ library that implements smoothing and mapping (SAM) in robotics and vision, using Factor Graphs and Bayes Networks as the underlying computing paradigm rather than sparse matrices."
3. Gtsam is a 15 year old academic library of robotics math that is actively maintained and updated.

What do those mean?
If you ever looked at a robot vacum, you'd realise it has the same needs as my project but worse,
e.g. it has some noisy sensors, and it needs to figure out where it is while building a map of the world.
Thats exactly connecting a bunch of uncertain estimates, and needing it fast because you want to put the robots
battery life on motion.


Gtsam has a lot of features and capabilties, but I think there are 2 shining ones (Lie groups and Factor graphs) and a new one
that made it the obvious choice for me (Hybrid models). Let's define what those mean
### Lie Groups

Rotations are a good example,  We represnt rotations as 3d matrices
but we can't combine them like we can with any 3d matrix. To see what I mean, hold a book
and rotate it to the right and then again away from you. So the bottom of the book is no facing you.
Now flip the order, rotate the book away from you and then to the right and now the back spine is facing you.

And that means that when I want to take "derivaives" of rotations, I can't use the standard "euclidean" machinary from pytorch.
Math does have a solution for this, called Lie Algebras, and a major part of Gtsam is providing these Lie-Primitives, so that we can
take derivatives that are geometrically coorect.

## Factor Graphs
Factor graphs are a way to represent "the factors and observations that influence our beliefs  about the things we care about".
I care about where my robot is in space, and some factors that influence it are how much the robot moved and what it sees.
But tracking the relationship between everything I saw at everypoint is intractable, sow e break it up into sparse factors, and because we are'nt sure about our beliefs and measuremetns, we add nise to capture it.

For example, the robot gets an image and sees a door. In 2d, the top right of the door is at (100,100) and the bottom right is at (70,102) . I think doors are 200cm tall give or take and that doors are on a wall (which has an extreme value ) .
So I can map (70,102)->(x,0,max_z) and (100,100)->(x,200,max_z) , and again, I can throw in some noise where I am not certain.

Those are all beliefs and prio knoweldge of mine, and I can also start off with some assumed camera position and pose, and check if the points I set in 3d project back to the points I set in 2d, upto noise. Combined with the Lie group mechanics we talked about, we can "propgate" that error to fix the camera pose .

If you're coming from Gradient Descent this might sound familiar, and it is, but note the differnces. This is very very sparse (2 points, and 9 degrees of freedom ) and very informative (we know a lot about our points and their geometry, as oppsoed to SGD which knows nothing.)
gtsam has all sorts of processes to take our beliefs and observations and give us an estimate of the true values of thigns, as well as uncertainty measures (derived from covariance )

## Hybrid Models
The third thing gtsam has that was relevant to me is Hybid models, the ability to
mix discrete variables with continuous ones. For instance a room might have 4 or 6 walls or more, a wall might have 0,1,2 or more doors on it, a standard cieling is 240,255 or 280 high but never 266 .

Being able to mix discete variables with continuous ones is a huge deal. Number of walls has to be an integer, and assuming 4 walls always is a sure way to be very wrong very fast, but we don't know upfront, and we might not know from a picture alone.
A better example, consider a wall X in a bathroom. P(X has door)=1/(num_rooms) as a prior.
But P(x has door| Bath or Toilet on X ) <0.1 because it's convenient to run a water pipeo along the full wall so a door and faucet/toilet along the same wall would make construction hard and expensive .


## Why did I choose gtsam ?
Remember, my goal is to get precise room measurements from one photo and the users description alongside prior knowledge,
and I want to quantify my uncertainty.
Factor graphs, as we saw , area  convenient and fast way to express beliefs and uncertainty.
Working with images, and desciptions require dealing with poses of cameras (polural, because the user is describing things from one or more points of view) and propogating errors trough the, . e.g. Lie Groups help.

Finnaly, room architecture benefits from discrete assumptions like has doors, num walls, is kitchen etc .

There are alternatives that are better for probabalistci work, for geomtry (maybe) and for hybrid modelling, but I couldn'T
find a single alternative that packaged all of those things together.
And I like that gtsam is old, because it means that they already got the bugs in the really important things solved. I will never
actually have to reason about or calculate a Lie algebra operation.

I hit many rough edges and a huge learnign curve on this, and I am fortunate to have the time to plough through it.
It does work though, and I think the pain I would go through getting fast probablasitc and geomtric modelling in some other way
would be much harder, because I would need to close much larger theoretical gaps (e.g. know about Lie algebras enough to know when I need them )


## Gtsam best features
### GenericProjectionFactor 2d Image worhorse
This is **the** factor that will tie things in pictures to the "model" of the world
that the robot has, via the camera. We give it as input a point in our 2d image,
and a point in the 3d world that the camera is "projecting" onto the 2d image.
We also provide a prior on the camera's pose (where it is in the world and how it is tilted)
and the camera intrinsics.
This creates a single factor that ties these variables together, and pushes everything
so that the "reprojection error", e.g. the error between where the paramterized camera landed and what we told is the truth.
#### Trick with GenericProjectionFactor
We often don't know the full 3d, coordinates, that's what we are trying to figure out.
But we can pretty easily figure out a floor or wall or cieling, and those have at least one
known coordinate (e.g floor has y=0), left wall has x=(0). So we can make "paramterized" Point3
like (This pseudo code that will not actually work )
```python
pixel_noise = gtsam.noiseModel.Isotropic.Sigma(2, 10.0) # How confident are we about that pixel
K = Cal3_S2(500.0, 500.0, 0.0, 320.0, 240.0) # Camera calibrations, should be optimized seperatly.

2d_point_measured = (100,200)
x,z,floor_point_1= (gtsam.Symbol(i) for i in range(3))
camera_pose_symbol = gtsam.Symbol()
floor_point_1_val=Point3(x,0,z) # Note, this should actual be a symbol, with a factor tying the point to the symbol
factor = gtsam.GenericProjectionFactorCal3_S2(measured_pt2,
    pixel_noise,
    floor_point_1,
    k,
    camera_pose_symbol
    )
```
Out if the box that wont quite work because `floor_point_1` needs to be a symbol
in the graph refering to a point and we need to add a custom factor that binds just thoise points
