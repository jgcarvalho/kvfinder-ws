# KVFinder web service

O kvfinder-ws é formado por três módulos. O módulo web, o módulo de fila e o módulo de execução. Cada
módulo é executado em um container (docker) separado. 

Para executar o kvfinder-ws é necessário o docker-compose:

    apt install docker-compose


O kvfinder é iniciado utilizando o comando abaixo na raiz do diretório desse repositório (onde está localizado o arquivo docker-compose.yml).

    docker-compose up 

ou 

    docker-compose up -d 

para executar em segundo plano.

Os comandos abaixo interrompem a execução do kvfinder-ws.

    docker-compose down 

ou 

    docker-compose down --volumes

para destruir os "volumes" que armazem os dados das filas e as pastas com os arquivos dos _jobs_.

Em execução o servidor web estará disponível em:

    http://localhost:8081/

E informações da fila poderão ser visualizadas em:

    http://localhost:8023/info

## API

#### Criar um job

`http://localhost:8081/create`

Método: `POST`  Media type: `application/json`

TODO: Descrever os campos do json de input...


#### Solicitar os resultados de um job

`http://localhost:8081/{id}`

Método: `GET`

Onde `{id}` é o __id__ recebido durante a submissão do _job_.

TODO: Descrever o json de output e exemplificar em diferentes estados de execução...

## Cliente integrado ao PyMOL: PyMOL KVFinder-web Tools

O cliente PyMOL KVFinder-web Tools está disponível em `client/PyMOL-KVFinder-web-Tools`.

Para mais informações, use o guia disponível [aqui](https://github.com/jvsguerra/kvfinder-ws/blob/master/client/PyMOL-KVFinder-web-tools/README.md)


## _Observações_

Após alterações nos códigos-fonte o sistema precisa ser recompilado com 

    docker-compose up --build

Para iniciar mais de um _worker_ e assim tornar o sistema capaz de executar
mais de 1 _job_ simultaneamente (exemplo com 2 _workers_). __Precisa de mais testes__.

    docker-compose up --scale kv-worker=2


Por ainda ser um sistema em fase de testes o tempo de _timeout_ de um _job_ está em __12 minutos__ e o tempo que esse _job_ permanece disponível ("_expires_after_") está em __6 minutos__. Em produção o _job_ deverá permanecer disponível por algo como __1 dia__.  
