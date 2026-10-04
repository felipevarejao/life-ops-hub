variable "github_client_id" {
  description = "Client ID do OAuth App do GitHub"
  type        = string
  sensitive   = true
}

variable "github_client_secret" {
  description = "Client Secret do OAuth App do GitHub"
  type        = string
  sensitive   = true
}

variable "github_admin_user" {
  description = "Usuário do GitHub com acesso Admin ao ArgoCD"
  type        = string
  default     = "felipevarejao"
}