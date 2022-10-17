# Distributed Systems

## About 
This is a collection of my distributed systems course projects from Distributed Systems (CPSC5220) at Seattle University, taught by Kevin Lundeen. 

### 1. Simple Client Server
Client connects to a Group Coordinator Daemon (GCD) which responds with a list of other clients who have joined the group. Client then sends a message to each member, prints their response, then exits. Client (client.py) written by me. Server (gcdserv.py) was written by and run remotely by the instructor. 

### 2. Bully Algorithm 
This project is an implementation of the Bully Algorithm, a method for asynchronously electing a leader node within a group of distributed processes ([Source: Wikipedia](https://en.wikipedia.org/wiki/Bully_algorithm)). The node attempts to reach consensus of who is the bully (leader) using asynch socket programming.

### 3. Detecting Arbitrage Opportunities Using Published Quotes (Pub/Sub) 
(In progress) A process that listens to currency exchange rates from a price feed and prints out a message whenver there is an arbitrage opportunity available. 
