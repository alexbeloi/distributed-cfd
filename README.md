# distributed-cfd
Code to do distributed stencil computations for high-dimensional fluid dynamics simulations.

### Current Status

Project halted until futher notice.

### Notes

Idea is to have a manager thread partition the initial solution state and distribute partition 'blocks' to worker nodes. The worker nodes do a round of computations and report back to manager that they have completed their work, at which time the manager orchestrates 'ghost cell' data exchange.
