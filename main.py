"""
<[Re] Recanatesi (2015). Neural Network Model of Memory Retrieval>
Copyright (C) <2019>  <de la Torre-Ortiz C, Nioche A>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os

import numpy as np
from tqdm import tqdm

import tools.plots as plot
import tools.sine_wave

FIG_DIR = "fig"
os.makedirs(FIG_DIR, exist_ok=True)

np.seterr(all="raise")

np.random.seed(123)

# === Parameters ===
# Architecture
num_neurons = 100000
num_memories = 16
# Activation
t_decay = 0.01
# Gain
threshold = 0
gain_exp = 2 / 5
# Hebbian rule
excitation = 13000
sparsity = 0.01
# Inhibition
sin_min = 0.7
sin_max = 1.06
t_oscillation = 1
phase_shift = 0.75
# Short term association
cont_forth = 1500
cont_back = 400
# Time
t_tot = 14
t_step = 0.001
# Noise
noise_var = 65
# Initialization
init_rate = 1
first_memory = 7
# Replication parameters
param_noise = 10
param_current = 4.75
# ==================


print("<[Re] Recanatesi (2015)>  Copyright (C) <2019>\n"
      "<de la Torre-Ortiz C, Nioche A>\n"
      "This program comes with ABSOLUTELY NO WARRANTY.\n"
      "This is free software, and you are welcome to redistribute it\n"
      "under certain conditions; see the 'LICENSE' file for details.\n")

# Compute memory patterns
print("Computing memory patterns and neuron populations...")
memory_patterns = np.random.choice([0, 1], p=[1 - sparsity, sparsity],
                                   size=(num_neurons, num_memories))

# Compute populations
pop, neurons_per_pop = np.unique([tuple(i) for i in memory_patterns],
                                 axis=0, return_counts=True)

num_pops = len(pop)

neurons_encoding = [(pop[:, mu] == 1).nonzero()[0] for mu in
                    range(num_memories)]

# === Other pre-computations ===
num_iter = int(t_tot / t_step)
relative_excitation = excitation / num_neurons
time_param = t_step / t_decay

# Inhibition
sine_wave = np.zeros(num_iter)

# Connectivity
forward_cont = np.arange(num_memories - 1)
backward_cont = np.arange(1, num_memories)

# Noise
noise = np.zeros((num_pops, num_iter))

# Neuron dynamics
firing_rates = np.zeros([num_pops])
current = np.zeros([num_pops])
average_firing_rates_per_memory = np.zeros((num_memories, num_iter))
currents = np.zeros((num_pops, num_iter))
currents_memory = np.zeros((num_memories, num_iter))
# ==============================

# Compute sine wave
print("Calculating inhibition values...")

for t in range(num_iter):
    sine_wave[t] = tools.sine_wave.sinusoid(
        min_=sin_min,
        max_=sin_max,
        period=t_oscillation,
        t=t,
        phase_shift=phase_shift * t_oscillation,
        dt=t_step
    )

inhibition = -sine_wave

# Compute weights
print("Computing regular, forward and backward connectivity...")

regular_connectivity = np.zeros((num_pops, num_pops))
forward_connectivity = np.zeros((num_pops, num_pops))
backward_connectivity = np.zeros((num_pops, num_pops))

for i in tqdm(range(num_pops)):
    for j in range(num_pops):
        regular_connectivity[i, j] = np.sum(
            (pop[i, :] - sparsity)
            * (pop[j, :] - sparsity)
        )

        forward_connectivity[i, j] = np.sum(
            pop[i, forward_cont] *
            pop[j, forward_cont + 1]
        )

        backward_connectivity[i, j] = np.sum(
            pop[i, backward_cont] *
            pop[j, backward_cont - 1]
        )

regular_connectivity *= excitation
forward_connectivity *= cont_forth
backward_connectivity *= cont_back
inhibition *= excitation

weights_without_inhibition = \
    regular_connectivity \
    + forward_connectivity \
    + backward_connectivity

# Compute noise
print("Calculating uncorrelated Gaussian noise...")

for pop in range(num_pops):
    noise[pop] = \
        np.random.normal(loc=0,
                         scale=(noise_var * neurons_per_pop[pop]) ** 0.5,
                         size=num_iter) / neurons_per_pop[pop] * param_noise


# Initialize firing rates
firing_rates[neurons_encoding[first_memory]] = init_rate

# Initialize current
c_ini = init_rate ** (1 / gain_exp) - threshold
current[neurons_encoding[first_memory]] = c_ini

# Compute neuron dynamics
print("Computing dynamics at each time step...")

for t in tqdm(range(num_iter)):

    # Update current
    for pop in range(num_pops):
        # Compute weights
        weights = (weights_without_inhibition[pop, :]
                   + inhibition[t]) / num_neurons

        # Compute input
        input_v = np.sum(weights[:] * neurons_per_pop[:] *
                         firing_rates[:])

        current[pop] += time_param * (
                -current[pop] + input_v
                + noise[pop, t])

        currents[pop, t] = current[pop]

    # Update firing rates
    firing_rates[:] = 0
    cond = (current + threshold) > 0
    firing_rates[cond] = (current[
                              cond] * param_current + threshold) ** gain_exp

    for p in range(num_memories):
        fr = firing_rates[neurons_encoding[p]]
        n_corresponding = neurons_per_pop[
            neurons_encoding[p]]

        average_firing_rates_per_memory[p, t] = \
            np.average(fr, weights=n_corresponding)

        c_mu = current[neurons_encoding[p]]

        currents_memory[p, t] = np.average(c_mu, weights=n_corresponding)

# Plots
print("Plotting...")
plot.currents(currents, dt=t_step,
              type_="population", fig_num=0)
plot.currents(currents_memory, dt=t_step,
              type_="memory", fig_num=1)

plot.firing_rates(average_firing_rates_per_memory,
                  dt=t_step)
plot.attractors(average_firing_rates_per_memory,
                dt=t_step)

plot.sine_wave(sine_wave, dt=t_step)
plot.inhibition(inhibition, dt=t_step)

plot.weights(weights_without_inhibition,
             type_="no_inhibition", fig_num=0)
plot.weights(regular_connectivity,
             type_="regular", fig_num=1)
plot.weights(forward_connectivity,
             type_="forward", fig_num=2)
plot.weights(backward_connectivity,
             type_="backward", fig_num=3)

plot.noise(noise, dt=t_step)
print("Done!")
