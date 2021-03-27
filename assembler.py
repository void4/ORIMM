from vm import *

def insert(a,o,b):
	if o + len(b) >= len(a):
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

def translate(program):

	lines = [{"source":line} for line in program.split("\n")]

	labels = {}
	opcount = 0

	print(lines)
	for no, line in enumerate(lines):
		clean = line["source"].strip().lower()

		# Remove comments
		if ";" in clean:
			clean = clean[:clean.find(";")]

		line["clean"] = clean

		opline = clean.split(" ")
		line["opline"] = opline
		print(line)
		if len(opline) == 0:
			continue
		elif len(opline) == 1 and opline[0].endswith(":"):
			line["type"] = "label"
			label = opline[0][:-1]
			line["name"] = label
			labels[label] = {"opc":opcount}
		elif (opindex:=opcode(opline[0])) is not None:
			line["type"] = "code"
			line["code"] = [opindex] + [intorlabel(arg) for arg in opline[1:]]
			opcount += 1 + I_ARGS[opindex]
		elif opline[0].upper() == "DB":
			line["type"] = "data"
			line["data"] = [intorlabel(arg) for arg in opline[1:]]
			opcount += len(opline[1:])
		elif opline[0]:
			raise Exception("Invalid symbol: ", opline[0], "Line", no)
		else:
			line["type"] = "whitespace"

		line["opcount"] = opcount


	# Calculate label offsets from expanded code
	offset = 0
	for line in lines:
		line["offset"] = offset
		if line["type"] == "label":
			labels[line["name"]] = offset
		elif line["type"] == "code":
			offset += len(line["code"])
		elif line["type"] == "data":
			offset += len(line["data"])

	# Replace all labels with their offsets
	for line in lines:
		if line["type"] == "code":
			for arg_index, arg in enumerate(line["code"][1:]):
				if arg in labels:
					line["code"][1+arg_index] = labels[arg]

	# Assemble
	binary = []

	for line in lines:
		if line["type"] == "code":
			binary += line["code"]
		elif line["type"] == "data":
			binary += line["data"]

	return binary
