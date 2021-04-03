from math import ceil

from vm import *

def insert(a,o,b):
	if o + len(b) > len(a):
		raise Exception("too long, exceeds memory size")

	i = 0
	for i in range(len(b)):
		a[o+i] = b[i]

	return o+i+1

def intorlabel(arg):
	try:
		return int(arg)
	except ValueError:
		return arg

def isint(v):
	try:
		int(v)
		return True
	except ValueError:
		return False

def translate(program):

	lines = [{"source":line} for line in program.split("\n")]

	labels = {}
	segments = {}
	opcount = 0

	DEFAULTVALUE = 0

	print(lines)
	for no, line in enumerate(lines):
		clean = line["source"].strip()#.lower()#can't lower cause of text

		# Remove comments
		if ";" in clean:
			clean = clean[:clean.find(";")]

		line["clean"] = clean

		opline = clean.split()
		line["opline"] = opline
		print(line)
		if len(opline) == 0:
			line["type"] = "whitespace"
		elif len(opline) == 1 and opline[0].endswith(":"):
			line["type"] = "label"
			label = opline[0][:-1]
			line["name"] = label
			#labels[label] = {"opc":opcount}
		elif len(opline)== 2 and opline[0] == "segment" or opline[0].startswith("segment@"):
			if not opline[1].endswith(":"):
				raise Exception("missing : in segment:", line, "Line", no)
			line["type"] = "segment"
			label = opline[1][:-1]
			line["name"] = label
			if "@" in opline[0]:
				line["offset"] = int(opline[0].split("@")[1])
			#segments[label] = {"opc":opcount}
		elif (opindex:=opcode(opline[0])) is not None:
			line["type"] = "code"
			line["code"] = [opindex] + [intorlabel(arg) for arg in opline[1:]]
			gotta = len(line["code"]) - 1
			have = I_ARGS[opindex]
			if gotta != have:
				raise Exception("Invalid number of args, gotta", gotta, "have", have, line, "Line", no)
			opcount += 1 + I_ARGS[opindex]
		elif opline[0].upper() == "DW":
			line["type"] = "data"
			line["data"] = [intorlabel(arg) for arg in opline[1:]]
			opcount += len(opline[1:])
		elif opline[0].upper() == "DS":
			line["type"] = "data"
			string = clean.split(" ", 1)[1]
			if not string.startswith('"') or not string.endswith('"'):
				raise Exception("Invalid DS string", "Line", no)
			bytes_per_word = BITS//8
			bytestr = (string[1:-1]+"\0").encode("utf8")
			# append 0 byte?
			wordstr = []
			for i in range(ceil(len(bytestr)/bytes_per_word)):
				wordstr.append(int.from_bytes(bytestr[i*bytes_per_word:i*bytes_per_word+bytes_per_word], byteorder="little"))#, bytes_per_word)
			print(wordstr)
			line["data"] = wordstr
		elif opline[0].upper() == "DZW":
			line["type"] = "data"
			line["data"] = [0 for i in range(int(opline[1]))]
			opcount += int(opline[1])
		elif opline[0]:
			raise Exception("Invalid symbol: ", opline[0], "Line", no)
		else:
			line["type"] = "whitespace"

		# XXX is opcount even used for anything?
		line["opcount"] = opcount


	# Calculate label offsets from expanded code
	offset = 0
	for line in lines:
		if "offset" in line:
			if line["offset"] < offset:
				raise Excepion("Overlapping offset")
			offset = line["offset"]
		else:
			line["offset"] = offset
		if line["type"] == "label":
			# do uniqueness check here or earlier
			if line["name"] in labels:
				raise Exception("Non-unique label name", line["name"])
			labels[line["name"]] = offset
		elif line["type"] == "segment":
			if line["name"] in segments:
				raise Exception("Non-unique segment name", line["name"])
			segments[line["name"]] = offset
		elif line["type"] == "code":
			offset += len(line["code"])
		elif line["type"] == "data":
			offset += len(line["data"])

	total_size = offset

	sorted_segments = sorted(segments.items(), key=lambda kv:kv[1])

	def segmentSize(name):
		for seg_index, (seg_name, seg_offset) in enumerate(sorted_segments):
			if seg_name == name:
				if seg_index < len(sorted_segments)-1:
					next_segment = sorted_segments[seg_index+1]
					segment_length = next_segment[1] - seg_offset
				else:
					segment_length = total_size - seg_offset
				return segment_length

	def translateName(name):
		if name in labels:
			return labels[arg]
		elif name in segments:
			return segments[name]
		elif name[0] == "#" and name[1:] in segments:
			return segmentSize(name[1:])
		elif ":" in name:
			segment_name, label_name = name.split(":")
			return labels[label_name] - segments[segment_name]

	# Replace all labels with their offsets
	for line in lines:
		if line["type"] == "code":
			for arg_index, arg in enumerate(line["code"][1:]):
				if isint(arg):
					pass
				else:
					line["code"][1+arg_index] = translateName(arg)
		elif line["type"] == "data":
			for data_index, data in enumerate(line["data"]):
				if isint(data):
					pass
				else:
					line["data"][data_index] = translateName(data)

	# Assemble

	binary = [None for i in range(total_size)]

	for line in lines:
		print(binary)
		print(line)
		if line["type"] == "code":
			insert(binary, line["offset"], line["code"])
			#binary += line["code"]
		elif line["type"] == "data":
			#binary += line["data"]
			insert(binary, line["offset"], line["data"])

	print("SEGMENTS")
	for seg_name, seg_offset in sorted_segments:
		print(seg_name, seg_offset, segmentSize(seg_name))

	binary = [i if i is not None else DEFAULTVALUE for i in binary]

	return binary
