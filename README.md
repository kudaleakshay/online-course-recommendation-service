# Build docker file 
	> docker build -t recommendation_system .

# Check docker images
	> docker images

# Run container or docker image in deaamon mode, so outside world can acess
	> docker run -it -d -p 5000:5000 recommendation_system

# Check running container
	> docker ps	 

# Open Browser and open 
    > http://127.0.0.1:5000/    