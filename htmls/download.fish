for i in (seq 1 100)
    wget -O $i.html https://montrealfringe.online.red61.ca/event/2030:$i/ || rm $i.html
end

