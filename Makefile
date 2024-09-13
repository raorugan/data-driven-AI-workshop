html:
	npx tailwindcss -i ./src/input.css -o ./src/html/css/output.css

runserver:
	npx http-server src/html --proxy http://localhost:7071 &
	cd src/api ; func host start -
