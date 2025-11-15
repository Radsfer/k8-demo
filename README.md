# Demo Kubernetes: Flask + StatefulSet + HPA

Este projeto demonstra dois conceitos fundamentais do Kubernetes usando uma aplicação simples em Python Flask:

1.  **Persistência de Dados (`StatefulSet`):** Como usar um `StatefulSet` e um `PersistentVolumeClaim (PVC)` para garantir que dados (de um banco SQLite) sobrevivam mesmo se o Pod falhar e for recriado.
2.  **Autoscaling (`HPA`):** Como usar um `HorizontalPodAutoscaler (HPA)` para escalar horizontalmente a aplicação (criar mais cópias/pods) automaticamente quando houver um pico de uso de CPU.

## O que há nos arquivos

  * **`app.py`:** Uma aplicação Flask com duas rotas:
      * `/`: Registra uma "visita" em um banco SQLite em `/data/app.db` e exibe todas as visitas. Usado para testar a persistência.
      * `/heavy`: Executa um loop de cálculo pesado para simular alta carga de CPU. Usado para testar o autoscaling.
  * **`Dockerfile`:** Constrói a imagem da aplicação Flask usando uma base Python 3.10-slim e expõe a porta 5000.
  * **`demo-k8s.yaml`:** O manifesto "tudo-em-um" do Kubernetes que cria três objetos:
    1.  `StatefulSet`: Gerencia o(s) pod(s) da aplicação, garantindo uma identidade estável e criando um Volume persistente para o banco de dados.
    2.  `Service`: Expõe a aplicação para o exterior do cluster usando um `NodePort`.
    3.  `HorizontalPodAutoscaler`: Monitora o uso de CPU dos pods e cria novas réplicas (até 5) se o uso médio passar de 30%.

## Pré-requisitos

Antes de começar, garanta que você tem as seguintes ferramentas instaladas e funcionando:

  * **Minikube:** Para criar um cluster Kubernetes local.
  * **kubectl:** A ferramenta de linha de comando para interagir com o Kubernetes.
  * **Docker:** (Ou outro driver que o Minikube possa usar para criar seu nó).

## Como Rodar a Demonstração

Siga estes passos para configurar e rodar o ambiente do zero.

### 1\. Inicie o Cluster Kubernetes

```bash
# Inicia o seu cluster Minikube
minikube start

# ATIVA O METRICS-SERVER (Obrigatório para o HPA funcionar!)
minikube addons enable metrics-server
```

### 2\. Construa a Imagem Docker

Precisamos construir a imagem da nossa aplicação e carregá-la no registro de Docker *interno* do Minikube.

```bash
# Aponta seu terminal para o ambiente Docker do Minikube
eval $(minikube -p minikube docker-env)

# Constrói a imagem a partir do Dockerfile
# (O '.' no final indica o diretório atual)
docker build -t flask-demo:v1 .
```

### 3\. Implante a Aplicação no Kubernetes

Agora, vamos aplicar nosso manifesto `demo-k8s.yaml` para criar todos os objetos.

```bash
# Aplica o arquivo YAML
kubectl apply -f demo-k8s.yaml
```

Para verificar se tudo subiu, você pode rodar (aguarde o `STATUS` ser `Running`):

```bash
kubectl get pods
```

-----

## Executando as Demos

Para executar os testes, primeiro precisamos do endereço IP e da porta do nosso serviço.

```bash
# Pega o URL do serviço
minikube service flask-service --url
```

(Guarde este URL, algo como `http://127.0.0.1:54321`, para os próximos passos).

### Demo 1: Persistência de Dados (StatefulSet)

Este teste prova que o banco de dados sobrevive a uma falha do pod.

1.  **Faça algumas visitas:**
    Acesse o URL (que você pegou acima) no seu navegador, ou use `curl` no terminal:

    ```bash
    curl http://127.0.0.1:54321/
    # Você verá "total_visits": 1

    curl http://127.0.0.1:54321/
    # Você verá "total_visits": 2
    ```

2.  **Simule uma falha (Delete o Pod):**

    ```bash
    kubectl delete pod flask-app-0
    ```

3.  **Observe o Pod ser recriado:**
    O `StatefulSet` garantirá que um novo pod `flask-app-0` seja criado para substituir o antigo. Você pode assistir isso acontecer com:

    ```bash
    kubectl get pods -w
    ```

    (Aguarde o novo pod voltar para o status `Running`).

4.  **Faça uma nova visita:**

    ```bash
    curl http://127.0.0.1:54321/
    ```

    **Resultado:** Você verá `"total_visits": 3`. As visitas 1 e 2 não foram perdidas\! O novo pod se conectou ao mesmo Volume (PVC) que o antigo usava.

### Demo 2: Autoscaling (HPA)

Este teste prova que o Kubernetes reage a picos de tráfego.

> **Recomendação:** Para esta demo, o ideal é ter 3 terminais abertos (ou usar um multiplexador como `tmux`) para observar tudo em tempo real.

  * **Terminal 1: Observe o HPA**

    ```bash
    kubectl get hpa -w
    # Aguarde a coluna TARGETS sair de <unknown> e mostrar a CPU (ex: 1%/30%)
    ```

  * **Terminal 2: Observe os Pods**

    ```bash
    kubectl get pods -w
    ```

  * **Terminal 3: Gere a Carga**
    Pegue o seu URL e adicione `/heavy` no final. Rode o loop abaixo para "atacar" o endpoint de carga:

    ```bash
    # Substitua pelo seu URL!
    while true; do curl http://127.0.0.1:54321/heavy; done
    ```

**O que observar:**

1.  **Terminal 1 (HPA):** A coluna `TARGETS` vai disparar (ex: `150%/30%`). A coluna `REPLICAS` mudará de `1` para `2`, `3`, etc.
2.  **Terminal 2 (Pods):** Você verá novos pods (`flask-app-1`, `flask-app-2`) sendo criados (`ContainerCreating` -\> `Running`).

Para parar o teste, pressione `Ctrl + C` no Terminal 3.

Após alguns minutos, você verá o HPA (Terminal 1) notar a queda de CPU e começar a reduzir as `REPLICAS`, e os pods extras (Terminal 2) serão `Terminating` (terminados).

-----

## Limpeza Total

Para parar e deletar todos os recursos criados:

```bash
# 1. Deleta os objetos do K8s (StatefulSet, Service, HPA)
kubectl delete -f demo-k8s.yaml

# 2. (IMPORTANTE) Deleta o Volume de dados
# O K8s não apaga volumes automaticamente
kubectl delete pvc db-storage-flask-app-0

# 3. Desliga o cluster
minikube stop
```
