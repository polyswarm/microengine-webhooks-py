{{/*
Expand the name of the chart.
*/}}
{{- define "microengine-webhooks-py.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "microengine-webhooks-py.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "microengine-webhooks-py.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "microengine-webhooks-py.labels" -}}
helm.sh/chart: {{ include "microengine-webhooks-py.chart" . }}
{{ include "microengine-webhooks-py.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "microengine-webhooks-py.selectorLabels" -}}
app.kubernetes.io/name: {{ include "microengine-webhooks-py.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Nginx labels
*/}}
{{- define "microengine-webhooks-py.nginx.labels" -}}
helm.sh/chart: {{ include "microengine-webhooks-py.chart" . }}
{{ include "microengine-webhooks-py.nginx.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Nginx selector labels
*/}}
{{- define "microengine-webhooks-py.nginx.selectorLabels" -}}
app.kubernetes.io/name: {{ include "microengine-webhooks-py.name" . }}-nginx
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Worker labels
*/}}
{{- define "microengine-webhooks-py.worker.labels" -}}
helm.sh/chart: {{ include "microengine-webhooks-py.chart" . }}
{{ include "microengine-webhooks-py.worker.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Worker selector labels
*/}}
{{- define "microengine-webhooks-py.worker.selectorLabels" -}}
app.kubernetes.io/name: {{ include "microengine-webhooks-py.name" . }}-worker
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "microengine-webhooks-py.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "microengine-webhooks-py.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
