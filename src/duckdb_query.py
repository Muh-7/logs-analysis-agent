import duckdb


class DuckDBLogQuery:

    def __init__(self, parquet_path: str):
        self.parquet_path = str(parquet_path)
        self.connection = duckdb.connect()

    
    def _fetch_dicts(self, cursor):
        """
        Convert DuckDB query results from tuples into dictionaries.
        """

        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()

        return [
            dict(zip(columns, row))
            for row in rows
        ]
    
    
    def count_events(self):
        result = self.connection.execute(
            """
            SELECT COUNT(*)
            FROM read_parquet(?)
            """,
            [self.parquet_path],
        ).fetchone()

        return result[0]

    def top_agents(self, limit: int = 10):
        return self.connection.execute(
            """
            SELECT
                agent_name,
                COUNT(*) AS event_count
            FROM read_parquet(?)
            WHERE agent_name IS NOT NULL
            GROUP BY agent_name
            ORDER BY event_count DESC
            LIMIT ?
            """,
            [self.parquet_path, limit],
        ).fetchall()

    def top_decoders(self, limit: int = 10):
        return self.connection.execute(
            """
            SELECT
                decoder,
                COUNT(*) AS event_count
            FROM read_parquet(?)
            WHERE decoder IS NOT NULL
            GROUP BY decoder
            ORDER BY event_count DESC
            LIMIT ?
            """,
            [self.parquet_path, limit],
        ).fetchall()

    def events_by_agent(
        self,
        agent_name: str,
        limit: int = 100,
    ):
        return self.connection.execute(
            """
            SELECT *
            FROM read_parquet(?)
            WHERE agent_name = ?
            LIMIT ?
            """,
            [
                self.parquet_path,
                agent_name,
                limit,
            ],
        ).fetchall()
    
    
    
    
    def http_method_summary(self):
        """
        Return the number of HTTP events grouped by HTTP method.

        Example:
            POST -> 50687
            GET  -> 13397
        """

        return self.connection.execute(
            """
            SELECT
                http_method,
                COUNT(*) AS event_count
            FROM read_parquet(?)
            WHERE http_method IS NOT NULL
            GROUP BY http_method
            ORDER BY event_count DESC
            """,
            [self.parquet_path],
        ).fetchall()


    def http_status_summary(self):
        """
        Return the number of HTTP events grouped by HTTP status code.

        Example:
            200 -> 61444
            404 -> 516
            502 -> 250
        """

        return self.connection.execute(
            """
            SELECT
                http_status,
                COUNT(*) AS event_count
            FROM read_parquet(?)
            WHERE http_status IS NOT NULL
            GROUP BY http_status
            ORDER BY event_count DESC
            """,
            [self.parquet_path],
        ).fetchall()
        
        
    def high_severity_events(self, min_level: int = 5, limit: int = 100):
        """
        Return security events with rule level >= min_level.
        """

        return self.connection.execute(
            """
            SELECT
                timestamp,
                agent_name,
                rule_id,
                rule_level,
                rule_description,
                source_ip,
                message
            FROM read_parquet(?)
            WHERE rule_level >= ?
            ORDER BY rule_level DESC, timestamp DESC
            LIMIT ?
            """,
            [self.parquet_path, min_level, limit],
        ).fetchall()


    def http_errors(self, min_status: int = 400, limit: int = 100):
        """
        Return HTTP requests with error status codes.
        """

        return self.connection.execute(
            """
            SELECT
                timestamp,
                agent_name,
                source_ip,
                http_method,
                http_status,
                http_host,
                http_uri
            FROM read_parquet(?)
            WHERE TRY_CAST(http_status AS INTEGER) >= ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            [self.parquet_path, min_status, limit],
        ).fetchall()


    def top_http_source_ips(self, limit: int = 10):
        """
        Return source IPs generating the most HTTP requests.
        """

        return self.connection.execute(
            """
            SELECT
                source_ip,
                COUNT(*) AS request_count
            FROM read_parquet(?)
            WHERE
                http_method IS NOT NULL
                AND source_ip IS NOT NULL
            GROUP BY source_ip
            ORDER BY request_count DESC
            LIMIT ?
            """,
            [self.parquet_path, limit],
        ).fetchall()
    
    
    
        
    def ip_activity(self, ip: str, limit: int = 100):
        """
        Return events associated with a specific source IP.
        """

        cursor = self.connection.execute(
            """
            SELECT
                timestamp,
                agent_name,
                decoder,
                rule_id,
                rule_level,
                rule_description,
                source_ip,
                source_port,
                http_method,
                http_status,
                http_host,
                http_uri,
                message
            FROM read_parquet(?)
            WHERE source_ip = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            [self.parquet_path, ip, limit],
        )

        return self._fetch_dicts(cursor)    
        
        
    
    
    
    def ip_summary(self, ip: str):
        """
        Return an aggregated summary of activity for a source IP.
        """

        summary = self.connection.execute(
            """
            SELECT
                COUNT(*) AS total_events,
                MIN(timestamp) AS first_seen,
                MAX(timestamp) AS last_seen,
                COUNT(DISTINCT agent_name) AS agents_count,
                COUNT(DISTINCT http_host) AS hosts_count,
                COUNT(DISTINCT http_uri) AS uris_count
            FROM read_parquet(?)
            WHERE source_ip = ?
            """,
            [self.parquet_path, ip],
        ).fetchone()

        cursor = self.connection.execute(
            """
            SELECT
                http_status,
                COUNT(*) AS count
            FROM read_parquet(?)
            WHERE
                source_ip = ?
                AND http_status IS NOT NULL
            GROUP BY http_status
            ORDER BY count DESC
            """,
            [self.parquet_path, ip],
        )

        status_codes = self._fetch_dicts(cursor)

        cursor = self.connection.execute(
            """
            SELECT
                http_host,
                COUNT(*) AS count
            FROM read_parquet(?)
            WHERE
                source_ip = ?
                AND http_host IS NOT NULL
            GROUP BY http_host
            ORDER BY count DESC
            LIMIT 10
            """,
            [self.parquet_path, ip],
        )

        hosts = self._fetch_dicts(cursor)

        cursor = self.connection.execute(
            """
            SELECT
                http_uri,
                COUNT(*) AS count
            FROM read_parquet(?)
            WHERE
                source_ip = ?
                AND http_uri IS NOT NULL
            GROUP BY http_uri
            ORDER BY count DESC
            LIMIT 20
            """,
            [self.parquet_path, ip],
        )

        uris = self._fetch_dicts(cursor)

        return {
            "ip": ip,
            "total_events": summary[0],
            "first_seen": summary[1],
            "last_seen": summary[2],
            "agents_count": summary[3],
            "hosts_count": summary[4],
            "uris_count": summary[5],
            "status_codes": status_codes,
            "top_hosts": hosts,
            "top_uris": uris,
        }
    def close(self):
        self.connection.close()