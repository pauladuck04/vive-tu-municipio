**justificaciones memoria**

Cada fragmento tiene dos copias en nodos distintos. El shard 0 tiene el primario (p) en es01 y la réplica (r) en es03. El shard 1 está en es03 y es02, y el shard 2 en es02 y es01. Elasticsearch nunca pone el primario y su réplica en el mismo nodo.
Cada nodo guarda dos fragmentos, un primario y una réplica. La carga queda equilibrada.
Si cae un nodo, los datos siguen completos. Por ejemplo, si cae es02, el shard 1 sigue disponible en es03 y el shard 2 en es01. Elasticsearch convierte la réplica en primario y sigue respondiendo. Lo comprobaremos en la prueba de tolerancia a fallos.