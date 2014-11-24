# this is obviously not the right place for this code, but I'm not sure where to put it
# You should have 'Rserve' installed, on linux something like this should work:
# sudo apt-get install r-cran-rserve
# Within R, you need to have 'amcatr' installed, which can be installed by calling R and running:
# install.packages("devtools"); library(devtools); install_github(repo="amcat-r", username="amcat")

# (I can't find out how to tell RServe to 'source' a file on loading without a conf file)
fn=`mktemp`
echo "source `pwd`/amcatrtest.r" > $fn
R CMD Rserve.dbg --RS-conf $fn
