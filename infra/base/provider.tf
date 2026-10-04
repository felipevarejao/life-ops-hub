  # Required providers - 
terraform {
  required_providers {
    kubernetes = { # Definir o provedor Kubernetes, que permite gerenciar recursos no cluster Kubernetes.
      source  = "hashicorp/kubernetes"
      version = "~> 3.2"
    }
    helm = { # Definir o provedor Helm, que permite gerenciar recursos do Helm no cluster Kubernetes.
      source  = "hashicorp/helm"
      version = "~> 3.3"
    }
    kubectl = { # Definir o provedor kubectl, que permite gerenciar recursos no cluster Kubernetes usando o comando kubectl.
      source  = "gavinbunney/kubectl"
      version = ">= 1.14.0"
    }
    time = { # Definir o provedor time, que permite trabalhar com recursos relacionados a tempo, como atrasos e temporizadores.
      source  = "hashicorp/time"
      version = "~> 0.7"
    }
  }
}


# Terraform Provider Configuration - Definir qual provedor será utilizado para gerenciar recursos na infraestrutura. Neste caso, estamos utilizando o provedor Kubernetes e Helm para gerenciar recursos no cluster Kubernetes.
provider "kubernetes" {
  config_path = "~/.kube/config"
}

provider "helm" {
  kubernetes = {
    config_path = "~/.kube/config"
  }
}

provider "kubectl" {
  config_path = "~/.kube/config"
}

provider "time" {
  # Configuração do provedor time, que permite trabalhar com recursos relacionados a tempo, como atrasos e temporizadores.
}
