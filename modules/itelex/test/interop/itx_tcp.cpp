// itx_tcp - the station's call logic (itx::Session) on a POSIX socket, for
// interoperability tests against other i-Telex implementations (piTelex).
//
//   itx_tcp listen <port> [--expect TEXT] [--reply TEXT] [--answerback AB]
//   itx_tcp call <host> <port> [--send TEXT] [--wru] [--expect TEXT]
//
// Prints every event on stdout ("RX ...", "WRU", "END reason") and exits 0
// only if everything asked for happened: the expected text arrived, the reply
// or text was sent and acknowledged, and the call ended cleanly.

#include <arpa/inet.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <poll.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

#include "itx_session.h"

using namespace itx;

static int g_fd = -1;
static std::string g_rx;
static std::string g_end;
static int g_wru = 0;

static uint32_t nowMs() {
  timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (uint32_t)(ts.tv_sec * 1000u + ts.tv_nsec / 1000000u);
}

static size_t tWrite(void *, const uint8_t *d, size_t n) {
  ssize_t w = ::send(g_fd, d, n, MSG_NOSIGNAL | MSG_DONTWAIT);
  return w < 0 ? 0 : (size_t)w;
}
static void tConn(void *, bool ascii) { std::printf("CONNECTED %s\n", ascii ? "ascii" : "i-telex"); }
static void tChar(void *, uint32_t cp) {
  char u[4];
  g_rx.append(u, utf8Put(cp, u));
}
static void tWru(void *) { g_wru++; std::printf("WRU\n"); }
static void tEnd(void *, const char *r) { g_end = r; std::printf("END %s\n", r); }

static const char *arg(int argc, char **argv, const char *name) {
  for (int i = 1; i + 1 < argc; i++)
    if (!std::strcmp(argv[i], name)) return argv[i + 1];
  return nullptr;
}
static bool flag(int argc, char **argv, const char *name) {
  for (int i = 1; i < argc; i++)
    if (!std::strcmp(argv[i], name)) return true;
  return false;
}

int main(int argc, char **argv) {
  if (argc < 3) {
    std::fprintf(stderr, "usage: itx_tcp listen <port> ... | itx_tcp call <host> <port> ...\n");
    return 2;
  }
  setvbuf(stdout, nullptr, _IOLBF, 0);
  const bool listening = !std::strcmp(argv[1], "listen");
  const char *expect = arg(argc, argv, "--expect");
  const char *reply = arg(argc, argv, "--reply");
  const char *text = arg(argc, argv, "--send");
  const char *answerback = arg(argc, argv, "--answerback");
  const bool wru = flag(argc, argv, "--wru");
  const int timeoutS = arg(argc, argv, "--timeout") ? std::atoi(arg(argc, argv, "--timeout")) : 30;

  if (listening) {
    int s = socket(AF_INET, SOCK_STREAM, 0);
    int one = 1;
    setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
    sockaddr_in a{};
    a.sin_family = AF_INET;
    a.sin_port = htons((uint16_t)std::atoi(argv[2]));
    a.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(s, (sockaddr *)&a, sizeof a) || listen(s, 1)) { perror("listen"); return 2; }
    std::printf("LISTENING %s\n", argv[2]);
    g_fd = accept(s, nullptr, nullptr);
    close(s);
  } else {
    addrinfo hints{}, *res = nullptr;
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    if (getaddrinfo(argv[2], argv[3], &hints, &res) || !res) { std::printf("END no-such-host\n"); return 1; }
    g_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (connect(g_fd, res->ai_addr, res->ai_addrlen)) { perror("connect"); return 1; }
    freeaddrinfo(res);
  }
  int one = 1;
  setsockopt(g_fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);

  SessionConfig cfg;
  if (answerback) cfg.answerback = answerback;
  SessionHandlers h;
  h.write = tWrite; h.onConnected = tConn; h.onChar = tChar; h.onWru = tWru; h.onEnd = tEnd;
  Session ss;
  ss.begin(listening ? Session::Role::Called : Session::Role::Caller, false, "", cfg, h, nowMs());
  ss.setAutoPrinted(true);

  bool sent = false, replied = false, asked = false, hungUp = false;
  size_t printedTo = 0;
  const uint32_t deadline = nowMs() + (uint32_t)timeoutS * 1000u;
  while (ss.state() != Session::State::Closed && (int32_t)(nowMs() - deadline) < 0) {
    pollfd p{g_fd, POLLIN, 0};
    poll(&p, 1, 10);
    if (p.revents & (POLLIN | POLLHUP | POLLERR)) {
      uint8_t buf[256];
      ssize_t n = recv(g_fd, buf, sizeof buf, 0);
      if (n > 0) ss.feed(buf, (size_t)n, nowMs());
      else { ss.transportClosed(); break; }
    }
    ss.poll(nowMs());
    for (size_t k; (k = g_rx.find('\n', printedTo)) != std::string::npos; printedTo = k + 1)
      std::printf("RX %s\n", g_rx.substr(printedTo, k - printedTo).c_str());

    if (!listening && text && !sent) { ss.send(text); ss.send("\r\n"); sent = true; }
    if (!listening && wru && sent && !asked && ss.sendQueueEmpty()) { ss.sendWru(); asked = true; }
    const bool gotExpected = !expect || g_rx.find(expect) != std::string::npos;
    if (listening && reply && gotExpected && !replied) { ss.send(reply); ss.send("\r\n"); replied = true; }
    // The caller rings off once it has what it came for and all is acknowledged.
    if (!listening && sent && gotExpected && ss.sendQueueEmpty() && ss.inFlight() == 0 && !hungUp) {
      ss.hangup();
      hungUp = true;
    }
  }
  if (printedTo < g_rx.size()) std::printf("RX %s\n", g_rx.substr(printedTo).c_str());
  close(g_fd);

  const bool gotExpected = !expect || g_rx.find(expect) != std::string::npos;
  bool ok = gotExpected && ss.state() == Session::State::Closed;
  if (listening && reply) ok = ok && replied;
  if (!listening) ok = ok && (g_end == "hangup");
  std::printf("RESULT %s (expected %s, end '%s')\n", ok ? "PASS" : "FAIL",
              gotExpected ? "seen" : "missing", g_end.c_str());
  return ok ? 0 : 1;
}
