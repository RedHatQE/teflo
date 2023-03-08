#!/bin/bash
for arg in "$@"
do
index=$(echo $arg | cut -f1 -d=)
val=$(echo $arg | cut -f2 -d=)
case $index in
X) x=$val;;

Y) y=$val;;

*)
esac
done
((result=x+y))
if [ $result -ne 30 ]; then
   echo "warning: result is not equal to 30."
   exit 2
else	
   echo "X+Y=$result"
   exit 0
fi
