from __future__ import print_function

from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from deap import gp

from pylab import *

import os
import pickle
import operator

import neat
import pygame
import numpy

import gamerun
import plot_utils
import visualize

import argparse
import traceback

from gp_train import AgentSimulator, eval_function, laser_distance, exec2, exec3, if_then_else


# def f1():
#     return pset.addTerminal(gamerun.battleship.x)


# def f2():
#     return pset.addTerminal(gamerun.battleship.vel)


# def f3():
#     return pset.addTerminal(gamerun.battleship.health)


# def f4():
#     return pset.addTerminal(gamerun.aliens_x[0])


# def f5():
#     return pset.addTerminal(gamerun.aliens_x[1])


# def f6():
#     return pset.addTerminal(gamerun.laser_x[0])


# def f7():
#     return pset.addTerminal(gamerun.laser_y[0])


# def f8():
#     return pset.addTerminal(gamerun.laser_x[1])


# def f9():
#     return pset.addTerminal(gamerun.laser_y[1])


# def f10():
#     return pset.addTerminal(gamerun.laser_x[2])


# def f11():
#     return pset.addTerminal(gamerun.laser_y[2])


# def f12():
#     return pset.addTerminal(gamerun.laser_x[3])


# def f13():
#     return pset.addTerminal(gamerun.laser_y[3])


# def f14():
#     return pset.addTerminal(gamerun.laser_x[4])


# def f15():
#     return pset.addTerminal(gamerun.laser_y[4])


# def f16():
#     return pset.addTerminal(gamerun.laser_x[5])


# def f17():
#     return pset.addTerminal(gamerun.laser_y[5])


def simulate_game(show_game, net=None, program=None, routine=None):
    gamerun.show_game = show_game
    if gamerun.show_game:
        pygame.init()
        # gamerun.clock = pygame.time.Clock()
        gamerun.gamebg = pygame.image.load('data/bg.jpg')
        gamerun.lasersound = pygame.mixer.Sound('data/laser.wav')
        gamerun.hitsound = pygame.mixer.Sound('data/hit.wav')

        screen_width = 700
        screen_height = 550
        win = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption('NEAT Spaceship!')

    else:
        win = None

    gamerun.frames = 0
    # gamerun.seccount = 0
    gamerun.totaltestseconds = 0

    gamerun.shootloop = 0
    gamerun.alienkills = 0
    gamerun.level = 1
    gamerun.spaceshipkills = 0
    gamerun.colorcounter = 0
    gamerun.timee = ''
    gamerun.ru = True
    # gamerun.pausebutton = False
    gamerun.show1 = True
    gamerun.spawnaliens = True
    gamerun.addalien = False
    gamerun.holdingpowerup = False
    gamerun.usepowerup = False
    gamerun.poweruploop = 0

    gamerun.aliennumber = 2
    gamerun.alienhealth = 10
    gamerun.alienlaserdamage = 1
    gamerun.alienvelocity = 1.3

    gamerun.battleship = gamerun.Spaceship()
    gamerun.lasers = []
    gamerun.enemy_lasers = []
    gamerun.aliens = []
    gamerun.enemy_spaceships = []
    gamerun.keys = {
        gamerun.K_LEFT: False,
        gamerun.K_RIGHT: False,
        gamerun.K_SPACE: True
    }
    gamerun.battleship_healths = []
    gamerun.aliens_x = [0, 0, 0]
    gamerun.laser_x = [0, 0, 0, 0, 0, 0]
    gamerun.laser_y = [0, 0, 0, 0, 0, 0]
    gamerun.enemy_spaceships_x = [0]

    game = True
    while game:
        result = gamerun.run(win, net=net, program=program, routine=routine)
        if result == 0:
            game = False

    # if gamerun.level > s.readlevel():
    #     s.save(gamerun.level, gamerun.alienkills, gamerun.spaceshipkills, gamerun.timee, gamerun.totaltestseconds)
    # elif gamerun.totaltestseconds > s.readseconds() and gamerun.level == s.readlevel():
    #     s.save(gamerun.level, gamerun.alienkills, gamerun.spaceshipkills, gamerun.timee, gamerun.totaltestseconds)

    # TODO find the best fitness based on gamerun.level, gamerun.alienkills, gamerun.spaceshipkills, gamerun.frame
    # fitness = (gamerun.level - 1) * 100 + gamerun.alienkills * 10 + gamerun.spaceshipkills * 50 # - gamerun.frames // 100000
    
    # health_fitness = 0
    # h_prec = gamerun.battleship_healths[0]
    # for i, h in enumerate(gamerun.battleship_healths[1:]):
    #     health_fitness += (h_prec - h)**2
    # health_fitness += gamerun.battleship_healths[-1]**2
    # health_fitness /= 10.0

    fitness = gamerun.alienkills * 10 + gamerun.spaceshipkills * 50
    # fitness = gamerun.alienkills * 100 + gamerun.spaceshipkills * 500 - gamerun.frames / 10000.0 - health_fitness
    # fitness = gamerun.frames

    print(f"{fitness} -> {gamerun.level} {gamerun.alienkills} {gamerun.spaceshipkills} {gamerun.frames} {gamerun.battleship_healths}")  # TODO valutare se rimuove il numero di frame dal fitness? (kind of penalty for escaping?)
    # TODO magari valutare i colpi dati ai nemici (da massimizzare) e minimizzare quelli andati a vuoto?
    # TODO magari valutare i colpi presi dai nemici (da minimizzare, i.e., subirli più avanti in livelli più complessi)?
    return fitness
    # TODO reason if makes sense to have a stopping criterion related to time (and not only death) --> this will be translated in find the best score for the considered max time


def eval_genomes(genomes, config):
    for genome_id, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        genome.fitness = simulate_game(show_game=False, net=net)


def evalArtificialAgent(individual):
    # Transform the tree expression to functionnal Python code
    routine = gp.compile(individual, pset)
    # Run the generated routine
    return simulate_game(show_game=False, program=agent, routine=routine),


def load_best():
    genome, network = None, None
    if os.path.isdir('runs/best/'):
        for filename in os.listdir('runs/best/'):
            if 'network' in filename:
                network = pickle.load(open(f"runs/best/{filename}", "rb"))
            elif 'genome' in filename:
                genome = pickle.load(open(f"runs/best/{filename}", "rb"))

    return genome, network


def save_best(genome, network):
    now = f"{datetime.datetime.now().isoformat()}".replace(':', '.')
    dirname = f"runs/{now}_fitness_{genome.fitness}"
    os.mkdir(dirname)
    pickle.dump(genome, open(f"{dirname}/genome.pkl", "wb"))
    pickle.dump(network, open(f"{dirname}/network.pkl", "wb"))
    visualize.draw_net(config, genome, filename=f"{dirname}/representation", view=False)

    best_genome, _ = load_best()
    if best_genome is None or best_genome.fitness < genome.fitness:
        if not os.path.isdir('runs/best/'):
            os.mkdir('runs/best/')

        pickle.dump(genome, open(f"runs/best/genome.pkl", "wb"))
        pickle.dump(network, open(f"runs/best/network.pkl", "wb"))
        visualize.draw_net(config, genome, filename=f"runs/best/representation", view=False)


GP_POP_SIZE = 50               # population size for GP
GP_NGEN = 10                    # number of generations for GP
GP_CXPB, GP_MUTPB = 0.5, 0.2    # crossover and mutation probability for GP
GP_TRNMT_SIZE = 7               # tournament size for GP
GP_HOF_SIZE = 2                 # size of the Hall-of-Fame for GP


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="NEAT Spaceship")
    parser.add_argument("--run_best", action="store_true", help="Run the best individual found")
    parser.add_argument("--neat", action="store_true", help="Run the NEAT algorithm for training of the NN")
    parser.add_argument("--gp", action="store_true", help="Run the GP algorithm for finding a program")
    parser.add_argument("--config_file", type=str, default="config.txt", help="Run the NEAT algorithm for training of the NN")
    parser.add_argument("--num_runs", type=int, default=1, help="The number of runs")
    parser.add_argument("--num_generations", type=int, default=10, help="The number of generations for each run")
    args = parser.parse_args()

    if args.neat:
        # Load configuration.
        local_dir = os.path.dirname(__file__)
        config_file = os.path.join(local_dir, args.config_file)
        config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_file)

        if args.num_runs == 1:
            # Create the population.
            p = neat.Population(config)

            # Add a stdout reporter to show progress in the terminal.
            stats = neat.StatisticsReporter()
            p.add_reporter(neat.StdOutReporter(True))
            p.add_reporter(stats)

            # Run NEAT for num_generations.
            try:
                genome = p.run(eval_genomes, args.num_generations)
            except Exception as e:
                traceback.print_exc()
                genome = p.best_genome
            except KeyboardInterrupt:
                genome = p.best_genome

            # Display the winning genome.
            print(f"\nBest genome:\n{genome}")

            # Create the winning network.
            network = neat.nn.FeedForwardNetwork.create(genome, config)

            # Simulate the game with the winning network and showing it.
            show_game = True
            best_fitness = simulate_game(show_game=show_game, net=network)
            print(f"\nBest fitness simulation:\n{best_fitness}")

            save_best(genome, network)
            if show_game:
                pygame.quit()

        else:
            results = []
            best_fitnesses = []
            try:
                for i in range(args.num_runs):
                    print(f"run {i + 1}/{args.num_runs}")

                    # Create the population.
                    p = neat.Population(config)

                    # Add a stdout reporter to show progress in the terminal.
                    stats = neat.StatisticsReporter()
                    p.add_reporter(neat.StdOutReporter(True))
                    p.add_reporter(stats)

                    # Run NEAT for num_generations.
                    genome = p.run(eval_genomes, args.num_generations)

                    # Display the winning genome.
                    print(f"\nBest genome:\n{genome}")

                    # Store best fitness for statistical analysis.
                    best_fitnesses.append(genome.fitness)

                    # Create the winning network.
                    network = neat.nn.FeedForwardNetwork.create(genome, config)

                    save_best(genome, network)

            except Exception as e:
                print(e)

            results.append(best_fitnesses)
            fig = figure("NEAT-Spaceship")
            ax = fig.gca()
            ax.boxplot(results)
            ax.set_ylabel("Best fitness")
            show()

    if args.gp:
        agent = AgentSimulator()

        pset = gp.PrimitiveSetTyped("MAIN", [float]*17, bool)
        pset.addPrimitive(if_then_else, [bool, float, float], float)
        # pset.addPrimitive(operator.add, 2)
        # pset.addPrimitive(operator.sub, 2)
        pset.addPrimitive(operator.gt, [float, float], bool)
        pset.addPrimitive(operator.eq, [float, float], bool)
        pset.addPrimitive(operator.neg, [bool], bool)
        pset.addPrimitive(operator.add, [float, float], float)
        pset.addPrimitive(operator.sub, [float, float], float)
        pset.addPrimitive(operator.mul, [float, float], float)

        # pset.addPrimitive(eval_function, [dict], float)
        # pset.addPrimitive(exec2, 2)
        # pset.addPrimitive(exec3, 3)
        # pset.addPrimitive(exec_while, 2)
        # pset.addTerminal(agent.action_left)
        # pset.addTerminal(agent.action_left_and_fire)
        # pset.addTerminal(agent.action_still)
        # pset.addTerminal(agent.action_still_and_fire)
        # pset.addTerminal(agent.action_right)
        # pset.addTerminal(agent.action_right_and_fire)
        # pset.addTerminal(laser_distance, dict)
        pset.addTerminal(5.0, float)
        pset.addTerminal(10.0, float)
        pset.addTerminal(15.0, float)
        pset.addTerminal(20.0, float)
        pset.addTerminal(25.0, float)
        pset.addTerminal(30.0, float)
        pset.addTerminal(35.0, float)
        pset.addTerminal(40.0, float)
        pset.addTerminal(True, bool)
        pset.addTerminal(False, bool)

        # # TODO probably we should teach the program how to use the terminal set (if it does not manage to learn it by itself)
        # pset.addTerminal(f1)
        # pset.addTerminal(f2)
        # pset.addTerminal(f3)
        # pset.addTerminal(f4)
        # pset.addTerminal(f5)
        # pset.addTerminal(f6)
        # pset.addTerminal(f7)
        # pset.addTerminal(f8)
        # pset.addTerminal(f9)
        # pset.addTerminal(f10)
        # pset.addTerminal(f11)
        # pset.addTerminal(f12)
        # pset.addTerminal(f13)
        # pset.addTerminal(f14)
        # pset.addTerminal(f15)
        # pset.addTerminal(f16)
        # pset.addTerminal(f17)
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()

        # Attribute generator
        toolbox.register("expr_init", gp.genFull, pset=pset, min_=1, max_=2)

        # Structure initializers
        toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr_init)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("evaluate", evalArtificialAgent)
        toolbox.register("select", tools.selTournament, tournsize=GP_TRNMT_SIZE)
        toolbox.register("mate", gp.cxOnePoint)
        toolbox.register("expr_mut", gp.genFull, min_=0, max_=2)
        toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)
        pop = toolbox.population(n=GP_POP_SIZE)
        hof = tools.HallOfFame(GP_HOF_SIZE)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", numpy.mean)
        stats.register("std", numpy.std)
        stats.register("min", numpy.min)
        stats.register("max", numpy.max)

        final_pop, logbook = algorithms.eaSimple(pop, toolbox, GP_CXPB, GP_MUTPB, GP_NGEN, stats, halloffame=hof)

        # plot GP tree
        nodes, edges, labels = gp.graph(hof[0])
        plot_utils.plotTree(nodes, edges, labels, "best", 'results')

        # plot fitness trends
        plot_utils.plotTrends(logbook, "best", 'results')

        # --------------------------------------------------------------------

        print("Best individual GP is %s, fitness %s" % (hof[0], hof[0].fitness.values))

        routine = gp.compile(hof[0], pset)
        simulate_game(show_game=True, program=agent, routine=routine),


    if args.run_best:
        genome, network = load_best()
        if network is None:
            print("network not present")
        else:
            best_fitness = simulate_game(show_game=True, net=network)
            print(f"\nBest fitness simulation:\n{best_fitness}")
            pygame.quit()

