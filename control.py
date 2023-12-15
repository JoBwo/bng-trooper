import subprocess

process = subprocess.Popen(['bngblaster', '-C', 'test.json'], stdout=subprocess.PIPE, encoding='utf8', bufsize=1)

while True:
    output = process.stdout.readline().strip()
    if len(output) == 0 and process.poll() is not None:
        break
    if output and len(output) > 0:
        print('The other script printed: ' + output)
returnCode = process.poll()
print('The other script ended with return code: ' + str(returnCode))