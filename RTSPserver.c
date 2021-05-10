/* GStreamer
 * Copyright (C) 2008 Wim Taymans <wim.taymans at gmail.com>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
 * Boston, MA 02110-1301, USA.
 */

#include <gst/gst.h>

#include <gst/rtsp-server/rtsp-server.h>

#include <stdio.h>

#define DEFAULT_RTSP_PORT "8000"

#define UDPSINK_PORT 5000

static char *port = (char *) DEFAULT_RTSP_PORT;
int inPort;
int outPort;
char outPortStr[100]= {0,};

static GOptionEntry entries[] = {
  {"port", 'p', 0, G_OPTION_ARG_STRING, &port,
      "Port to listen on (default: " DEFAULT_RTSP_PORT ")", "PORT"},
  {NULL}
};

int
main (int argc, char *argv[])
{

  GMainLoop *loop;
  GstRTSPServer *server;
  GstRTSPMountPoints *mounts;
  GstRTSPMediaFactory *factory;
  GOptionContext *optctx;
  GError *error = NULL;
  char udpsrc_pipeline[512];
  int tt = 0;

  gst_init(&argc, &argv);

  if (argc < 3) {
    g_print("Usage:\n./RTSPserver inPort:XXXX outPort:YYYY\n");
    return -1;
  }

  if (sscanf(argv[1], "inPort:%d", &inPort) != 1)
  {
    g_print("Error! First argument should be inPort:XXXX, where XXXX - port number\n");
    return -1;
  }

  if (sscanf(argv[2], "outPort:%d", &outPort) != 1)
  {
    g_print("Error! Second argument should be outPort:XXXX, where XXXX - port number\n");
    return -1;
  }
  sprintf(outPortStr, "%d", outPort);

  sprintf(udpsrc_pipeline,
   "( udpsrc name=pay0 port=%d caps=\"application/x-rtp, media=video, "
   "clock-rate=90000, encoding-name=H265, payload=96 \" )", inPort);
  loop = g_main_loop_new (NULL, FALSE);

  /* create a server instance */
  server = gst_rtsp_server_new ();
  g_object_set (server, "service", outPortStr, NULL);

  /* get the mount points for this server, every server has a default object
   * that be used to map uri mount points to media factories */
  mounts = gst_rtsp_server_get_mount_points (server);

  /* make a media factory for a test stream. The default media factory can use
   * gst-launch syntax to create pipelines.
   * any launch line works as long as it contains elements named pay%d. Each
   * element with pay%d names will be a stream */
  factory = gst_rtsp_media_factory_new ();
  gst_rtsp_media_factory_set_launch (factory, udpsrc_pipeline);
  gst_rtsp_media_factory_set_shared (factory, TRUE);

  /* attach the test factory to the /test url */
  gst_rtsp_mount_points_add_factory (mounts, "/video", factory);

  /* don't need the ref to the mapper anymore */
  g_object_unref (mounts);

  /* attach the server to the default maincontext */
  gst_rtsp_server_attach (server, NULL);

  /* start serving */
  g_print ("stream ready at rtsp://127.0.0.1:%d/video\n", outPort);
  g_main_loop_run (loop);

  return 0;
}
