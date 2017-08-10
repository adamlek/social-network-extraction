# -*- coding: utf-8 -*-
"""
Created on Tue Feb  7 16:54:00 2017

Author: Adam Ek
Contact: adek2204@student.su.se / df90aqx@gmail.com
Comments: Social Network Extraction

INPUT: file.conll, tagged with stagger3.0
OUTPUT: Something something dark side

Linje 486 i all_21.txt: Om aftonen träffade Johan Pelle och Måns i Röda Rummet. saknas KOMMA!!!!
"""
from networkana import TextFormatter, AnaphoraResolutor
from collections import defaultdict, Counter
import networkx as nx
import scipy.stats as st
#from networkx_viewer import Viewer

class TextReader():
    def __init__(self, k=False):
        ### search ranges and text
        if k:
            self.context_size = k
        else:
            self.context_size = 3
        self.current_text = []

        ### NamedEntityRecogn results
        self.ners = defaultdict(set)

        ### current_actor
        self.source = []
        self.sentence_context = []

        ### person_entity_dictionaries
        self.entities = defaultdict(dict)
        self.ent_counts = defaultdict(int)
        self.ent_keywords = defaultdict(dict)

        self.wc = defaultdict(int)
        self.graph = 0

    # files to read
    def read_file(self, file, nerfile):
        # read textfile
        with open(file) as text:
            self.current_text.append([]) #initial sentence
            for index, line in enumerate(text):
                if line.split():
                    self.current_text[-1].append(line.split('\t')) # add line to current paragraph
#                    print(line)
                else:
                    self.current_text.append([]) # create new paragraph
                    
        # read NER file
        with open(nerfile) as text:
            for index, line in enumerate(text):
                if line.split():
                    line = line.split('\t')
                    self.ners[line[0]].add(line[1].rstrip('\n'))
#                    print(line)

        self.generate_socialnetwork()

        return self.entities

    def generate_socialnetwork(self):
        # Iterate over text
        skipper = []
        looplist = list(self.current_text)
        for i, sentence in enumerate(looplist):
            skipper = []
            self.sentence_context = []
            for n, word in enumerate(sentence):
                if word[1] not in ['!','.',',','?']:
                    self.wc[word[1]] += 1

                if not word or n in skipper:
#                    print(word[2])
                    continue
                
#                if word[3] == 'PROPN' or word[1] == 'Flod':
#                    self.ent_counts[word[2]] += 1


                if word[3] == 'PROPN' or word[2] == 'flod':
                    if n+1 != len(sentence):
                        if sentence[n+1][3] == 'PROPN':
                            if str(word[2] + ' ' + sentence[n+1][2]) in self.ners['person']:
                                skipper.append(n+1)
#                                print(str(word[2] + ' ' + sentence[n+1][2]))
    
                    if word[2] != 'flod':
                        if word[2] not in self.ners['person']:
                            continue
#                        else:
#                            self.pers_count[word[2]] += 1

                    self.ent_counts[word[2]] += 1

                    
                    if word[2] not in self.ners['person']:
                        continue

                    #add source word
                    self.source = word

                    if word[2] not in self.entities.keys():
                        self.entities[word[2]] = defaultdict(int)
                        self.ent_keywords[word[2]] = defaultdict(int)

                    context = [self.current_text[i][:n]]
                    for f in range(1, self.context_size):
                        if i-f >= 0:
                            context.append([])
                            for w in self.current_text[i-f]:
                                context[-1].append(w)

                    self.read_context(context)

    # add connections
    def read_context(self, context):
        for sentence in context:
            for k, w in enumerate(sentence):
                if w[3] == 'PROPN':
                    if not w[2][0].isupper():
                        continue

                    if w[2] not in self.ners['person']:
                        continue
                    
                    # avoid adding entity twice, e.g. Sherlock Holmes, "Sherlock" and "Holmes"
                    if k-1 > 0:
                        if sentence[k-1][3] == 'PROPN':
                            continue
                        
                    # skip self-reference
                    if w[2] != self.source[2]:
                        # co-occurence
                        self.entities[self.source[2]][w[2]] += 1
                        if w[-4] == self.source[-4]:
                            # dependent on same word
                            self.entities[self.source[2]][w[2]] += 1


    def create_graph(self, data, min_node_size = False):
        G = nx.Graph()
        data['Arvid Falk'] = Counter(data['Falk']) + Counter(data['Bror Falk']) + Counter(data['Arvid']) + Counter(data['Arvid Falk'])
        del data['Bror Falk']
        del data['Falk']
        del data['Arvid']
        
        data['Nicolaus'] = Counter(data['Carl Nicolaus']) + Counter(data['Carl Falk']) + Counter(data['Nicolaus Falk']) + Counter(data['Nicolaus'])
        del data['Carl Nicolaus']
        del data['Carl Falk']
        del data['Nicolaus Falk']
        
        data['Fritz Levin'] = Counter(data['Fritz Levin']) + Counter(data['Levinen']) + Counter(data['Levis']) + Counter(data['Levi'])
        del data['Levi']
        del data['Levis']
        del data['Levinen']
        
        data['Olle Montanus'] = Counter(data['Olof Montanus'])
        del data['Olof Montanus']
        
        data2 = dict(data)
        for w in data2:
            if ' ' in w:
                ww = w.split(' ')
                for t in data2:
                    if t in ww:
#                        print(w, '<<', t)
                        data[w] = Counter(data[w]) + Counter(data[t])
#                        print(w, '<', t)
                        del data[t]
                    elif t.endswith('s') and t[:-1] in ww:
                        data[w] = Counter(data[w]) + Counter(data[t])
                        del data[t]
        
                        
        for name in data.keys():
            G.add_node = name
        for i, source in enumerate(data):
            for target in data[source]:
                if target not in data.keys():
                    continue
                # add keyword connections
                kword_score = 0
                for w in self.ent_keywords[source].keys():
                    if w in self.ent_keywords[target].keys():
                        kword_score += 1
                        self.type[1] += 1
        
                if G.has_edge(source, target):
                    G[source][target]['weight'] += (data[source][target] + kword_score)
                else:
                    G.add_edge(source, target, weight = (data[source][target] + kword_score))
                if G.has_edge(source, target):
                    G[source][target]['weight'] += (kword_score)
                else:
                    G.add_edge(source, target, weight = (kword_score))
        return G

    def centrality(self, graph):
        deg = nx.degree_centrality(graph)
        bet = nx.betweenness_centrality(graph)
        eig = nx.eigenvector_centrality(graph)

        return deg, bet, eig


if __name__ == '__main__':
    loldict = defaultdict(set)
    for number in [100,200,300]:

#        tr1 = TextReader(number)
#        ent1 = tr1.read_file('/home/adam/august/data/socialnetworkdata/hemso/hsopreprocessed.conll',
#                           '/home/adam/august/data/socialnetworkdata/hemso/hsoNER.txt')
#        tr2 = TextReader(number)
#        ent2 = tr2.read_file('/home/adam/august/data/socialnetworkdata/hemso/hsoanaphor.conll',
#                           '/home/adam/august/data/socialnetworkdata/hemso/hsoNER.txt')
        tr1 = TextReader(number)
        ent1 = tr1.read_file('/home/adam/august/data/socialnetworkdata/roda/rodapreprocessed.conll',
                           '/home/adam/august/data/socialnetworkdata/roda/rodaNER.txt')
        tr2 = TextReader(number)
        ent2 = tr2.read_file('/home/adam/august/data/socialnetworkdata/roda/rodaanaphor.conll',
                           '/home/adam/august/data/socialnetworkdata/roda/rodaNER.txt')
        
        
#        characters = ['Carlsson', 'flod', 'Gusten', 'Rundqvist', 'Norman', 
#                      'Clara', 'Lotten', 'Norström', 'Ida']
        characters = ['Arvid Falk', 'Olle Montanus', 'Bror Sellén', 'Lundell', 'Ygberg', 
                      'Kristus Rehnhjelm', 'Henrik Borg', 'Fritz Levin', 'Struve', 
                      'Nicolaus']
    
        
        g1rank = {k:[0,0,0] for k in characters}
    #    print(g1rank)
        
        graph1 = tr1.create_graph(ent1)
        graph2 = tr2.create_graph(ent2) 
        
        

        
        for node in graph2.nodes():
    #        print(node)
            if node not in graph1.nodes():
                graph2.remove_node(node)
        
        for w in graph1.nodes():
            loldict[number].add(w)
        
        
        deg, bet, eig = tr1.centrality(graph2)
        ranking = []
        ranks = 0
        for a,b,c in zip(sorted(deg.items(), key=lambda x: x[1], reverse=True),
                         sorted(bet.items(), key=lambda x: x[1], reverse=True),
                         sorted(eig.items(), key=lambda x: x[1], reverse=True)):
            ranks += 1
    #        print((ranks,a,b,c))
            if a[0] in g1rank.keys():
                g1rank[a[0]][0] = ranks 
                
            if b[0] in g1rank.keys():
                g1rank[b[0]][1] = ranks 
                
            if c[0] in g1rank.keys():
                g1rank[c[0]][2] = ranks 
                
            ranking.append((a,b,c))
            
        
        deg_list = [0]*len(g1rank.keys())
        bet_list = [0]*len(g1rank.keys())
        eig_list = [0]*len(g1rank.keys())
        for num, (pers, positions) in enumerate(g1rank.items()):
            deg_list[num] = positions[0]
            bet_list[num] = positions[1]
            eig_list[num] = positions[2]
            print(pers, positions)
            
        print(deg_list, '\n',
              bet_list, '\n', 
              eig_list)
        
#        main = [1,2,3,4,5,6,7,8,9]
        main = [1,2,3,4,5,6,7,8,9,10]
        print(st.stats.spearmanr(main, deg_list))
        print(st.stats.spearmanr(main, bet_list))
        print(st.stats.spearmanr(main, eig_list))
            
    
    #    _scores = []
    #    _rank = []
    #    for node in graph1:
    #        scores = [0,0,0]
    #        rank = [0,0,0]
    #        for i, item in enumerate(ranking):
    #            for ii, subitem in enumerate(item):
    #                if subitem[0] == node:
    #                    if ii == 0:
    #                        scores[0] = subitem[1]
    #                        rank[0] = i
    #                    elif ii == 1:
    #                        scores[1] = subitem[1]
    #                        rank[1] = i
    #                    elif ii == 2:
    #                        scores[2] = subitem[1]
    #                        rank[2] = i
    #                    else:
    #                        pass
    ##        print(node,',', scores[0],',', scores[1],',', scores[2])
    #        _scores.append(scores)
    
        
    #    for n1 in graph_a:
    #        print(graph_n[n1])
        nx.write_gexf(graph1, 'c{0}.gexf'.format(number))
        nx.write_gexf(graph2, 'c{0}.gexf'.format(number))           
#        nx.write_gexf(graph1, 'hsograph_normal_{0}.gexf'.format(number))
#        nx.write_gexf(graph2, 'hsograph_anaph_{0}.gexf'.format(number))
#        print(len(graph1.nodes()), len(graph2.nodes()))
    
#    print(loldict[6]-loldict[3])
#    print(loldict[9]-loldict[3])

