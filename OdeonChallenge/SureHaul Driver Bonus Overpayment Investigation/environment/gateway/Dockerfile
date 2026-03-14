FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY main.go .
RUN CGO_ENABLED=0 GOOS=linux go build -o gateway main.go

FROM alpine:3.18

WORKDIR /app
COPY --from=builder /app/gateway .

EXPOSE 8080

CMD ["./gateway"]
