(defproject ev3-client "0.1.0-SNAPSHOT"
  :description "FIXME: write description"
  :url "http://example.com/FIXME"
  :license {:name "EPL-2.0 OR GPL-2.0-or-later WITH Classpath-exception-2.0"
            :url "https://www.eclipse.org/legal/epl-2.0/"}
  :dependencies [[org.clojure/clojure "1.11.2"]
                 [org.clojure/core.async "1.6.681"]
                 [org.clojure/data.json "0.2.0"]
                 [nrepl "1.1.0"]]
  :main ^:skip-aot ev3-client.core
  :target-path "target/%s"
  :profiles {:uberjar {:aot :all
                       :jvm-opts ["-Dclojure.compiler.direct-linking=true"]}}

  :plugins [[jonase/eastwood "0.3.5"]
            [cider/cider-nrepl "0.50.2"]]
  )


