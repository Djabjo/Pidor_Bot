
{{/* Common names */}}
{{- define "bot.fullname" -}}
{{- printf "%s-bot" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Common labels */}}
{{- define "bot.labels" -}}
team: bot
app.kubernetes.io/name: {{ include "bot.fullname" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
helm.sh/chart: {{ include "bot.chart" . }}
app.kubernetes.io/version: {{ .Chart.Version }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
{{- define "bot.chart" -}}{{ .Chart.Name }}{{- end -}}


{{/* Selector labels */}}
{{- define "bot.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bot.fullname" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}


{{/* PostgreSQL Helpers */}}
{{- define "my-postgres.fullname" -}}
{{- printf "%s-postgres" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "my-postgres.labels" -}}
app.kubernetes.io/name: postgres
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "my-postgres.selectorLabels" -}}
app.kubernetes.io/name: postgres
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "my-postgres.pvcName" -}}
{{- printf "%s-postgres-pvc" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}