--
-- PostgreSQL database dump
--

-- Dumped from database version 14.18 (Homebrew)
-- Dumped by pg_dump version 14.18 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: image; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.image (
    id integer NOT NULL,
    path character varying(200),
    label character varying(10),
    "timestamp" timestamp without time zone,
    label_manual boolean,
    timestamp_manual boolean,
    location_manual boolean,
    dark_ratio double precision,
    edge_density double precision,
    contour_count double precision,
    color_diversity double precision,
    avg_saturation double precision,
    bright_ratio double precision,
    std_intensity double precision,
    entropy double precision,
    color_clusters double precision,
    aspect_dev double precision,
    fill_ratio double precision,
    location_id integer NOT NULL,
    user_id integer NOT NULL
);


--
-- Name: image_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.image_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: image_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.image_id_seq OWNED BY public.image.id;


--
-- Name: location; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.location (
    id integer NOT NULL,
    address character varying(200),
    longitude double precision,
    latitude double precision
);


--
-- Name: location_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.location_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: location_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.location_id_seq OWNED BY public.location.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    name character varying(200),
    mail character varying(200),
    password character varying(300),
    is_admin boolean,
    is_superadmin boolean
);


--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: image id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image ALTER COLUMN id SET DEFAULT nextval('public.image_id_seq'::regclass);


--
-- Name: location id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.location ALTER COLUMN id SET DEFAULT nextval('public.location_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Data for Name: image; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.image (id, path, label, "timestamp", label_manual, timestamp_manual, location_manual, dark_ratio, edge_density, contour_count, color_diversity, avg_saturation, bright_ratio, std_intensity, entropy, color_clusters, aspect_dev, fill_ratio, location_id, user_id) FROM stdin;
58	app/static/uploads/WhatsApp Image 2021-01-29 at 6.23.22 PM_1.jpeg	full	2025-07-07 00:36:26.828447	f	f	f	0	0	0	0	0	0	0	0	0	0	0	62	1
59	app/static/uploads/b4582c0689d487a40b80d52f2bfb5abfa9304228.temp_1.jpeg	empty	2025-06-24 23:03:30.115592	f	f	f	0	0	0	0	0	0	0	0	0	0	0	63	1
60	app/static/uploads/00517_04_1.jpg	empty	2025-07-04 20:33:33.183197	f	f	f	0	0	0	0	0	0	0	0	0	0	0	64	1
61	app/static/uploads/WhatsApp Image 2020-07-11 at 8.43.02 PM (1)_1.jpeg	full	2025-06-24 20:25:35.167716	f	f	f	0	0	0	0	0	0	0	0	0	0	0	65	1
62	app/static/uploads/02587_03_1.jpg	empty	2025-07-07 14:16:37.426451	f	f	f	0	0	0	0	0	0	0	0	0	0	0	66	1
63	app/static/uploads/WhatsApp Image 2020-10-26 at 9.19.14 AM (1)_1.jpeg	empty	2025-07-01 13:26:39.370839	f	f	f	0	0	0	0	0	0	0	0	0	0	0	67	1
64	app/static/uploads/01300_00_1.jpg	empty	2025-06-20 00:34:42.234522	f	f	f	0	0	0	0	0	0	0	0	0	0	0	68	1
65	app/static/uploads/5282.full_1.jpeg	full	2025-06-09 01:07:44.264456	f	f	f	0	0	0	0	0	0	0	0	0	0	0	69	1
66	app/static/uploads/WhatsApp Image 2020-05-09 at 3.57.59 PM_1.jpeg	empty	2025-06-11 12:10:46.441579	f	f	f	0	0	0	0	0	0	0	0	0	0	0	70	1
67	app/static/uploads/3f53a459-b46f-4e87-90ac-f9e43cc23320_2.jpeg	empty	2025-06-24 07:57:48.402603	f	f	f	0	0	0	0	0	0	0	0	0	0	0	71	1
68	app/static/uploads/WhatsApp Image 2020-11-02 at 7.23.13 PM (5)_1.jpeg	full	2025-06-11 20:37:50.504313	f	f	f	0	0	0	0	0	0	0	0	0	0	0	72	1
69	app/static/uploads/00547_06_1.jpg	empty	2025-06-27 08:33:52.611182	f	f	f	0	0	0	0	0	0	0	0	0	0	0	73	1
70	app/static/uploads/WhatsApp Image 2020-10-04 at 10.35.23 AM (9)_1.jpeg	empty	2025-06-18 04:39:55.778307	f	f	f	0	0	0	0	0	0	0	0	0	0	0	74	1
71	app/static/uploads/00566_03_1.jpg	empty	2025-06-12 22:24:58.010315	f	f	f	0	0	0	0	0	0	0	0	0	0	0	75	1
72	app/static/uploads/WhatsApp Image 2020-05-09 at 9.56.49 AM (2)_1.jpeg	empty	2025-06-25 07:40:02.195733	f	f	f	0	0	0	0	0	0	0	0	0	0	0	76	1
73	app/static/uploads/00569_03_1.jpg	empty	2025-06-16 19:02:04.239671	f	f	f	0	0	0	0	0	0	0	0	0	0	0	77	1
74	app/static/uploads/WhatsApp Image 2020-07-06 at 9.41.53 AM (1)_1.jpeg	empty	2025-07-08 10:52:06.165675	f	f	f	0	0	0	0	0	0	0	0	0	0	0	78	1
75	app/static/uploads/WhatsApp Image 2020-05-24 at 5.24.32 PM (6)_1.jpeg	empty	2025-06-08 06:53:08.394433	f	f	f	0	0	0	0	0	0	0	0	0	0	0	79	1
76	app/static/uploads/WhatsApp Image 2020-05-09 at 2.08.14 PM_1.jpeg	empty	2025-06-30 12:44:10.461981	f	f	f	0	0	0	0	0	0	0	0	0	0	0	80	1
77	app/static/uploads/401.full_1.jpeg	empty	2025-06-22 18:05:13.086565	f	f	f	0	0	0	0	0	0	0	0	0	0	0	81	1
78	app/static/uploads/WhatsApp Image 2020-10-20 at 7.14.11 PM (10)_1.jpeg	empty	2025-06-20 14:46:15.31435	f	f	f	0	0	0	0	0	0	0	0	0	0	0	82	1
79	app/static/uploads/WhatsApp Image 2020-05-08 at 2.18.58 PM_1.jpeg	full	2025-07-05 11:38:17.54761	f	f	f	0	0	0	0	0	0	0	0	0	0	0	83	1
80	app/static/uploads/01906_01_1.jpg	empty	2025-06-16 10:17:19.421591	f	f	f	0	0	0	0	0	0	0	0	0	0	0	84	1
81	app/static/uploads/02136_04_1.jpg	empty	2025-07-06 16:07:21.428596	f	f	f	0	0	0	0	0	0	0	0	0	0	0	85	1
82	app/static/uploads/WhatsApp Image 2020-05-09 at 2.08.14 PM (6)_1.jpeg	empty	2025-06-27 07:45:23.391864	f	f	f	0	0	0	0	0	0	0	0	0	0	0	86	1
83	app/static/uploads/WhatsApp Image 2020-05-09 at 2.03.38 PM (3)_1.jpeg	empty	2025-06-16 21:39:25.385855	f	f	f	0	0	0	0	0	0	0	0	0	0	0	87	1
84	app/static/uploads/WhatsApp Image 2020-09-30 at 4.07.58 PM_1.jpeg	empty	2025-06-08 10:40:27.398024	f	f	f	0	0	0	0	0	0	0	0	0	0	0	88	1
85	app/static/uploads/WhatsApp Image 2020-10-20 at 7.29.51 PM (2)_1.jpeg	empty	2025-06-27 22:07:29.216844	f	f	f	0	0	0	0	0	0	0	0	0	0	0	89	1
86	app/static/uploads/WhatsApp Image 2020-05-09 at 2.03.38 PM (1)_1.jpeg	empty	2025-06-11 10:38:31.015775	f	f	f	0	0	0	0	0	0	0	0	0	0	0	90	1
87	app/static/uploads/01670_07_1.jpg	empty	2025-07-07 19:24:32.889441	f	f	f	0	0	0	0	0	0	0	0	0	0	0	91	1
88	app/static/uploads/86cd7cf4-726f-40c5-9788-89c890be3914_1.jpeg	empty	2025-06-29 19:58:34.977836	f	f	f	0	0	0	0	0	0	0	0	0	0	0	92	1
89	app/static/uploads/0dd71fdd2db2d0beb278eddb5692a156fb79a40c.temp_2.jpeg	full	2025-06-24 11:51:37.170952	f	f	f	0	0	0	0	0	0	0	0	0	0	0	93	1
90	app/static/uploads/02248_00_1.jpg	empty	2025-07-04 22:54:39.1822	f	f	f	0	0	0	0	0	0	0	0	0	0	0	94	1
91	app/static/uploads/WhatsApp Image 2020-09-24 at 8.49.45 AM (3)_1.jpeg	empty	2025-06-24 09:47:41.192508	f	f	f	0	0	0	0	0	0	0	0	0	0	0	95	1
92	app/static/uploads/WhatsApp Image 2020-05-18 at 11.21.17 AM (6)_1.jpeg	empty	2025-06-24 09:10:43.144295	f	f	f	0	0	0	0	0	0	0	0	0	0	0	96	1
93	app/static/uploads/00543_02_1.jpg	empty	2025-06-21 06:57:45.138231	f	f	f	0	0	0	0	0	0	0	0	0	0	0	97	1
94	app/static/uploads/WhatsApp Image 2020-09-21 at 8.53.14 AM_1.jpeg	empty	2025-06-27 16:49:47.126308	f	f	f	0	0	0	0	0	0	0	0	0	0	0	98	1
95	app/static/uploads/WhatsApp Image 2020-10-04 at 10.35.23 AM (6)_1.jpeg	empty	2025-06-18 03:27:48.985209	f	f	f	0	0	0	0	0	0	0	0	0	0	0	99	1
96	app/static/uploads/2752.full_1.jpeg	empty	2025-06-29 08:04:51.733718	f	f	f	0	0	0	0	0	0	0	0	0	0	0	100	1
97	app/static/uploads/WhatsApp Image 2020-05-09 at 2.08.15 PM (2)_1.jpeg	empty	2025-07-08 02:02:53.671248	f	f	f	0	0	0	0	0	0	0	0	0	0	0	101	1
98	app/static/uploads/WhatsApp Image 2020-05-09 at 2.03.37 PM (6)_1.jpeg	empty	2025-06-28 09:45:55.711726	f	f	f	0	0	0	0	0	0	0	0	0	0	0	102	1
99	app/static/uploads/00207_03_1.jpg	empty	2025-06-26 14:14:57.721094	f	f	f	0	0	0	0	0	0	0	0	0	0	0	103	1
100	app/static/uploads/00594_00_1.jpg	empty	2025-06-22 21:43:59.643503	f	f	f	0	0	0	0	0	0	0	0	0	0	0	104	1
101	app/static/uploads/WhatsApp Image 2020-10-14 at 10.34.29 PM_1.jpeg	empty	2025-06-15 10:04:01.554948	f	f	f	0	0	0	0	0	0	0	0	0	0	0	105	1
102	app/static/uploads/0e02598e-acbb-423e-912e-cf2b922b5bd7_2.jpeg	empty	2025-06-15 23:23:03.529608	f	f	f	0	0	0	0	0	0	0	0	0	0	0	106	1
103	app/static/uploads/WhatsApp Image 2020-05-24 at 5.18.12 PM (5)_1.jpeg	full	2025-06-28 18:24:05.953649	f	f	f	0	0	0	0	0	0	0	0	0	0	0	107	1
104	app/static/uploads/00217_05_1.jpg	empty	2025-06-13 15:01:08.20679	f	f	f	0	0	0	0	0	0	0	0	0	0	0	108	1
105	app/static/uploads/00204_00_1.jpg	empty	2025-07-05 02:04:10.260295	f	f	f	0	0	0	0	0	0	0	0	0	0	0	109	1
106	app/static/uploads/WhatsApp Image 2020-12-26 at 12.36.54 AM_1.jpeg	full	2025-06-08 21:29:12.393759	f	f	f	0	0	0	0	0	0	0	0	0	0	0	110	1
107	app/static/uploads/WhatsApp Image 2020-06-29 at 8.55.43 AM (1)_1.jpeg	empty	2025-06-19 14:58:14.554623	f	f	f	0	0	0	0	0	0	0	0	0	0	0	111	1
\.


--
-- Data for Name: location; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.location (id, address, longitude, latitude) FROM stdin;
62	Boulevard Saint-Germain, 75005 Paris (#8054)	2.3372	48.8462
63	Rue de Rivoli, 75001 Paris (#3591)	2.3522	48.8566
64	Avenue des Champs-Élysées, 75008 Paris (#6874)	2.2945	48.8714
65	Boulevard Saint-Germain, 75005 Paris (#9717)	2.3372	48.8462
66	Rue de Rivoli, 75001 Paris (#6660)	2.3522	48.8566
67	Place de la Bastille, 75011 Paris (#6710)	2.3693	48.8532
68	Place de la Bastille, 75011 Paris (#6610)	2.3693	48.8532
69	Rue de la Paix, 75002 Paris (#7972)	2.3312	48.8695
70	Rue de Rivoli, 75001 Paris (#4514)	2.3522	48.8566
71	Place de la Bastille, 75011 Paris (#3615)	2.3693	48.8532
72	Boulevard Saint-Germain, 75005 Paris (#5257)	2.3372	48.8462
73	Rue de Rivoli, 75001 Paris (#6496)	2.3522	48.8566
74	Boulevard Saint-Germain, 75005 Paris (#6559)	2.3372	48.8462
75	Place de la Bastille, 75011 Paris (#8923)	2.3693	48.8532
76	Rue de la Paix, 75002 Paris (#4521)	2.3312	48.8695
77	Avenue des Champs-Élysées, 75008 Paris (#3247)	2.2945	48.8714
78	Place de la Bastille, 75011 Paris (#9409)	2.3693	48.8532
79	Rue de la Paix, 75002 Paris (#9480)	2.3312	48.8695
80	Rue de la Paix, 75002 Paris (#5334)	2.3312	48.8695
81	Rue de la Paix, 75002 Paris (#8780)	2.3312	48.8695
82	Place de la Bastille, 75011 Paris (#5584)	2.3693	48.8532
83	Avenue des Champs-Élysées, 75008 Paris (#2942)	2.2945	48.8714
84	Rue de Rivoli, 75001 Paris (#3571)	2.3522	48.8566
85	Place de la Bastille, 75011 Paris (#4274)	2.3693	48.8532
86	Rue de la Paix, 75002 Paris (#4105)	2.3312	48.8695
87	Rue de Rivoli, 75001 Paris (#3479)	2.3522	48.8566
88	Rue de Rivoli, 75001 Paris (#5524)	2.3522	48.8566
89	Place de la Bastille, 75011 Paris (#6885)	2.3693	48.8532
90	Place de la Bastille, 75011 Paris (#9147)	2.3693	48.8532
91	Avenue des Champs-Élysées, 75008 Paris (#4301)	2.2945	48.8714
92	Boulevard Saint-Germain, 75005 Paris (#5455)	2.3372	48.8462
93	Avenue des Champs-Élysées, 75008 Paris (#3646)	2.2945	48.8714
94	Place de la Bastille, 75011 Paris (#5349)	2.3693	48.8532
95	Rue de la Paix, 75002 Paris (#7900)	2.3312	48.8695
96	Place de la Bastille, 75011 Paris (#2956)	2.3693	48.8532
97	Avenue des Champs-Élysées, 75008 Paris (#3769)	2.2945	48.8714
98	Rue de Rivoli, 75001 Paris (#3586)	2.3522	48.8566
99	Boulevard Saint-Germain, 75005 Paris (#9407)	2.3372	48.8462
100	Avenue des Champs-Élysées, 75008 Paris (#7226)	2.2945	48.8714
101	Place de la Bastille, 75011 Paris (#9594)	2.3693	48.8532
102	Rue de la Paix, 75002 Paris (#9551)	2.3312	48.8695
103	Rue de la Paix, 75002 Paris (#2514)	2.3312	48.8695
104	Place de la Bastille, 75011 Paris (#9183)	2.3693	48.8532
105	Boulevard Saint-Germain, 75005 Paris (#8729)	2.3372	48.8462
106	Boulevard Saint-Germain, 75005 Paris (#6894)	2.3372	48.8462
107	Rue de Rivoli, 75001 Paris (#1269)	2.3522	48.8566
108	Avenue des Champs-Élysées, 75008 Paris (#6557)	2.2945	48.8714
109	Rue de Rivoli, 75001 Paris (#8234)	2.3522	48.8566
110	Boulevard Saint-Germain, 75005 Paris (#2946)	2.3372	48.8462
111	Rue de Rivoli, 75001 Paris (#1402)	2.3522	48.8566
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."user" (id, name, mail, password, is_admin, is_superadmin) FROM stdin;
1	admin	admin@test.com	pbkdf2:sha256:1000000$vUhqcVYN$f90cab60eeae11b92d0da2372969d14259658509460f01e18a774fcde7805c66	t	t
\.


--
-- Name: image_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.image_id_seq', 107, true);


--
-- Name: location_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.location_id_seq', 111, true);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_id_seq', 1, true);


--
-- Name: image image_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_pkey PRIMARY KEY (id);


--
-- Name: location location_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.location
    ADD CONSTRAINT location_pkey PRIMARY KEY (id);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: image image_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_location_id_fkey FOREIGN KEY (location_id) REFERENCES public.location(id) ON DELETE CASCADE;


--
-- Name: image image_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

