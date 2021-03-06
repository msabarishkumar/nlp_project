from collections import defaultdict

import string

debug = False
only_features = True
word_of_interest = "brillian"

class AMRGraph:
	def __init__(self, node_map, edge_map, root, sentence=""):
		self.root = str(root)
		self.sentence = sentence
		self.node_map = node_map 
		self.edge_map = edge_map

		self.generate_features()

	def get_distance_from_root(self, root, depth, nodes_of_interest):		
		if root in nodes_of_interest:
			return set([depth])

		out = set()
		for (v, _) in self.edge_map[root]:
			out = out.union(self.get_distance_from_root(v, depth+1, nodes_of_interest))			
		return out
	
	def get_words_within_dis(self, nodes_of_interest, dis=1):
		for _ in range(dis):
			tmp = set(nodes_of_interest)
			for u in self.edge_map.keys():
				for (v, _) in self.edge_map[u]:
					if v in nodes_of_interest:
						tmp.add(u)
				if u in nodes_of_interest:
					tmp.update([v for v,_ in self.edge_map[u]])
			nodes_of_interest = tmp

		return [value for (key, value) in self.node_map.items() if key in nodes_of_interest]
		

	def generate_features(self):
		features = self.features = set()

		# label of the root node.
		features.add("root_" + self.node_map[self.root])

		nodes_of_interest = []
		for (node_id, word) in self.node_map.items():
			# add all the words in the graph.
			features.add("amr_word_" + word)

			# find all the nodes whose label is the word of interest.
			if word.startswith(word_of_interest):
				nodes_of_interest.append(node_id)
		
		# compute the distance from the root.
		for d in self.get_distance_from_root(self.root, 0, nodes_of_interest):
			features.add("distance_" + str(d))

		# find words within a distance of two from nodes of interest.
		for word in self.get_words_within_dis(set(nodes_of_interest), 2):
			features.add("radius2_" + word)

		# find words within a distance of three from nodes of interest.
		for word in self.get_words_within_dis(set(nodes_of_interest), 3):
			features.add("radius3_" + word)

		if len(nodes_of_interest):
			num_in_edge = num_out_edge = 0
			in_labels = defaultdict(int)
			out_labels = defaultdict(int)
			for u in self.edge_map.keys():
				if u == self.root:
					features.add("root_outdegree_" + str(len(self.edge_map[u])))					

				for (v, edge_label) in self.edge_map[u]:
					# get features corresponding to the root.
					if self.root == u:
						features.add("root_edgelabel_" + edge_label)					
	
					# v is the node of interest to us with the label we are looking for.
					if v in nodes_of_interest:
						# word belonging to node u.
						features.add("in_word_" + self.node_map[u])
						# features of the  form (u, edgelabel, v).
						features.add("amr_" + self.node_map[u] + "_" + edge_label + "_" + self.node_map[v])
						# label of the edge (u, v).
						features.add("in_edgelabel_" + edge_label)
						# count the number of edges pointing to v.
						num_in_edge += 1
						# count the number of incoming edges of each type.
						in_labels[edge_label] += 1
						# find all my siblings.
						for (sibling, _) in self.edge_map[u]:
							if not v == sibling:
								features.add("sibling_" + self.node_map[sibling])
				
					# v is the node to which our node of interest has an edge pointing to.
					if u in nodes_of_interest:
						# word belonging to node v.
						features.add("out_word_" + self.node_map[v])
						# features of the  form (u, edgelabel, v).
						features.add("amr_" + self.node_map[u] + "_" + edge_label + "_" + self.node_map[v])
						# label of the edge (u, v).
						features.add("out_edgelabel_" + edge_label)
						# count the number of edges pointing from u.
						num_out_edge += 1
						# count the number of outgoing edges of each type.
						out_labels[edge_label] += 1

			for (edge_label, in_count) in in_labels.items():
				features.add("in_edgelabel_" + edge_label + "_" + str(int(in_count/len(nodes_of_interest))))
				
			for (edge_label, out_count) in out_labels.items():
				features.add("out_edgelabel_" + edge_label + "_" + str(int(out_count/len(nodes_of_interest))))
			

			features.add("in_degree_"  + str(int(num_in_edge/len(nodes_of_interest))))
			features.add("out_degree_" + str(int(num_out_edge/len(nodes_of_interest))))
		
				
	def __str__(self):
		if not only_features:
			out = []
			out.append("Sentence: " + self.sentence)
			out.append("Root: " + self.root)
			out.append("Edge Map:\n" + str(self.edge_map))
			out.append("Node Map:\n" + str(self.node_map))
			out.append("Features:\n" + str(self.features))
			return "\n".join(out) + "\n"
		else: 
			return " ".join(list(self.features))
		

def split_line(line):
	out = []
	for w in filter(lambda x: len(x)>0, line.split(" ")):
		out.extend(filter(lambda x: len(x)>0, w.split("\t")))
	return out

def process_amr_input(node_details, edge_details, root, sentence):
	node_map = {}
	for node_info in node_details:
		tokens = split_line(node_info)
		letters = []
		for letter in tokens[3]:
			if not (letter == "-" or letter in string.digits):
				letters.append(letter)		
		node_map[tokens[2]] = "".join(letters)

	edge_map = defaultdict(list)
	for edge_info in edge_details:
		tokens = split_line(edge_info)
		# There is a directed edge from u->v in the graph.
		if len(tokens[5]) < len(tokens[6]):
			(u, v) = (tokens[5], tokens[6])
		else:
			(u, v) = (tokens[6], tokens[5])
		edge_map[u].append((v, tokens[3]))

	if not len(edge_details):
		for u in node_map.keys():
			for v in node_map.keys():
				if not u == v:
					if v.startswith(u) and len(v)<=len(u)+3:
						edge_map[u].append((v, "amr_edge"))

	graph = AMRGraph(node_map, edge_map, root, sentence)
	if debug:
		print graph

def parse_info(file_name):

	def process_graph(node_info, edge_info, root, sentence):
		if len(node_info):
			process_amr_input(node_info, edge_info, root, sentence) 
		elif len(sentence):
			print " ".join(list(set(map(lambda x: "amr_word_"+x, filter(lambda x: len(x)>0, sentence.split(" "))))))

        # Read the input file and process the data.
	with open(file_name) as file_:
		readFile, sentence, node_info, edge_info, root = (False, "", [], [], -1)
		
		for line in file_:
			line = line.strip()

			""" Once you parse amr output corresponding to a sentence
			    reset the variable readFile to False.
			"""
			if len(line) == 0:
				process_graph(node_info, edge_info, root, sentence)
				readFile, sentence, node_info, edge_info, root = (False, "", [], [], -1)

			if readFile:
				if "::node" in line:
					node_info.append(line)			
				if "::edge" in line:
					edge_info.append(line)
				if "::root" in line:
					root = split_line(line)[2]

			if "::snt" in line:
				readFile, sentence, node_info, edge_info, root = (True, line[7:].strip(), [], [], -1)

		process_graph(node_info, edge_info, root, sentence)

if __name__ == "__main__":
	import sys

	if len(sys.argv) < 1:
		print "input file name missing in the command line input"
	else:
		if len(sys.argv) > 2: debug = True

		file_name = sys.argv[1]	        
		parse_info(file_name)
