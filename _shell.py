import time
import zmq

context = zmq.Context()

#  Socket to talk to server
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

controller_file = "controller.txt"
with open(controller_file) as infile:
	controller_lines = infile.read().split('\n')
	controller = [(x.split(',')[0], int(x.split(',')[1])) for x in controller_lines if x.strip()]
	controller_string = '\n\t'.join([f"{i}.): {x[0]}" for i, x in enumerate(controller, start=1)])
	infile.close()

print(f"\n\t{controller_string}\n\n")
input_=input(f"\tInput: ").strip()
while input_.lower() != 'exit':
	if input_.isnumeric() and 1 <= eval(input_) <= len(controller):
		parameters = ','.join([input(f"\t\t{i}: ") for i in range(1, controller[eval(input_)-1][1]+1)])
		output = controller[eval(input_)-1][0]
		output += ',' + parameters if controller[eval(input_)-1][1] else ''

		socket.send(output.encode())
		message = socket.recv().decode()

		if message:
			print(f"\n{message}\n")
		print(f"\n\t{controller_string}\n\n")
	input_=input(f"\tInput: ").strip()


